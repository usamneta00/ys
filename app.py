from fastapi import FastAPI, File, UploadFile, Header, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import shutil
import json
import tempfile
from openai import OpenAI
from talk import AgenticNLToSQL
from config import CONFIG_DB
from cryptography.fernet import Fernet
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from jwt import encode, decode  # استيراد الدوال encode و decode بشكل صحيح
import hashlib




app = FastAPI()

# إضافة middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # يسمح بالوصول من أي مصدر
    allow_credentials=True,
    allow_methods=["*"],  # يسمح بجميع طرق HTTP
    allow_headers=["*"],  # يسمح بجميع الرؤوس
)

# إعداد المجلدات للقوالب والملفات الثابتة
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# إنشاء مفتاح التشفير - يجب تزينه بشكل آمن وإرساله للعميل بشكل آمن
encryption_key = b'cw_0x689RpI-jtRR7oE8h_eQsKImvJapLeSbXpwF4e4='

# تعريف مسار ملف التراخيص
LICENSES_FILE = "authorized_devices.json"

# تحويل مفتاح الترخيص إلى bytes
LICENSE_SECRET_KEY = b'cw_0x689RpI-jtRR7oE8h_eQsKImvJapLeSbXpwF4e4='

# إضافة المجلد لتخزين ملفات التراخيص
LICENSES_DIR = "licenses"
os.makedirs(LICENSES_DIR, exist_ok=True)

class RemoteLicenseManager:
    def __init__(self):
        self.licenses_file = LICENSES_FILE
        self.licenses_data = self.load_licenses()

    def load_licenses(self) -> Dict:
        """تحميل بيانات التراخيص من الملف"""
        try:
            if os.path.exists(self.licenses_file):
                with open(self.licenses_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"خطأ في تحميل ملف التراخيص: {e}")
            return {}

    def save_licenses(self):
        """حفظ بيانات التراخيص في الملف"""
        try:
            with open(self.licenses_file, 'w', encoding='utf-8') as f:
                json.dump(self.licenses_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"خطأ في حفظ ملف التراخيص: {e}")

    def generate_license_key(self, email: str, client_id: str, hardware_id: str, duration_days: int) -> str:
        """توليد مفتاح ترخيص مشفر"""
        license_data = {
            'email': email,
            'client_id': client_id,
            'hardware_id': hardware_id,  # إضافة معرف الجهاز
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(days=duration_days)).isoformat()
        }
        
        return encode(  # استخدام encode بدلاً من jwt.encode
            license_data,
            LICENSE_SECRET_KEY,
            algorithm="HS256"
        )

    def add_license(self, email: str, client_id: str, hardware_id: str, duration_days: int = 365) -> Optional[str]:
        """إضافة ترخيص جديد"""
        try:
            print("1. بدء إضافة الترخيص...")
            if email not in self.licenses_data:
                print("2. إنشاء سجل جديد للمستخدم")
                self.licenses_data[email] = {
                    "clients": [],
                    "created_at": datetime.now().isoformat()
                }

            # التحقق من عدد العملاء المسجلين
            print(f"3. عدد العملاء الحالي: {len(self.licenses_data[email]['clients'])}")
            if len(self.licenses_data[email]["clients"]) >= 3:
                print("4. تم تجاوز الحد الأقصى للعملاء")
                return None

            # التحقق من وجود العميل
            client_exists = False
            for client in self.licenses_data[email]["clients"]:
                if client["client_id"] == client_id:
                    print("5. العميل موجود مسبقاً")
                    # التحقق من معرف الجهاز
                    if client["hardware_id"] != hardware_id:
                        print("6. معرف الجهاز غير متطابق")
                        return None  # محاولة استخدام نفس المعرف مع جهاز مختلف
                    client["expires_at"] = (datetime.now() + timedelta(days=duration_days)).isoformat()
                    client["last_verified"] = datetime.now().isoformat()
                    client_exists = True
                    break

            if not client_exists:
                print("7. إضافة عميل جديد")
                # إضافة عميل جديد
                self.licenses_data[email]["clients"].append({
                    "client_id": client_id,
                    "hardware_id": hardware_id,
                    "created_at": datetime.now().isoformat(),
                    "expires_at": (datetime.now() + timedelta(days=duration_days)).isoformat(),
                    "last_verified": datetime.now().isoformat()
                })

            print("8. حفظ التغييرات")
            self.save_licenses()
            
            print("9. توليد مفتاح الترخيص")
            return self.generate_license_key(email, client_id, hardware_id, duration_days)
            
        except Exception as e:
            print(f"خطأ في إضافة الترخيص: {e}")
            return None

    def verify_license(self, license_key: str, hardware_id: str) -> Tuple[bool, str]:
        """التحقق من صلاحية الترخيص"""
        try:
            # فك تشفير مفتاح الترخيص
            license_data = decode(license_key, LICENSE_SECRET_KEY, algorithms=["HS256"])
            email = license_data.get('email')
            client_id = license_data.get('client_id')
            stored_hardware_id = license_data.get('hardware_id')
            
            if not email or not client_id or not stored_hardware_id:
                return False, "بيانات الترخيص غير صالحة"

            # التحقق من تطابق معرف الجهاز
            if stored_hardware_id != hardware_id:
                return False, "هذا الترخيص غير صالح لهذا الجهاز"

            if email not in self.licenses_data:
                return False, "لم يتم العثور على ترخيص لهذا المستخدم"

            for client in self.licenses_data[email]["clients"]:
                if client["client_id"] == client_id:
                    # التحقق من تاريخ الصلاحية
                    expires_at = datetime.fromisoformat(license_data['expires_at'])
                    if datetime.now() > expires_at:
                        return False, "الترخيص منتهي الصلاحية"
                    
                    return True, "الترخيص صالح"

            return False, "لم يتم العثور على ترخيص لهذا العميل"

        except jwt.ExpiredSignatureError:
            return False, "الترخيص منتهي الصلاحية"
        except jwt.InvalidTokenError:
            return False, "مفتاح الترخيص غير صالح"
        except Exception as e:
            print(f"خطأ في التحقق من الترخيص: {e}")
            return False, str(e)

class LicenseFileManager:
    """إدارة ملفات التراخيص المشفرة"""
    def __init__(self):
        self.encryption_key = encryption_key
        self.cipher_suite = Fernet(self.encryption_key)

    def create_license_file(self, email: str, license_key: str, hardware_id: str) -> Optional[str]:
        """إنشاء ملف الترخيص المشفر"""
        try:
            print("1. بدء إنشاء ملف الترخيص...")
            # إنشاء بيانات الترخيص
            license_data = {
                'email': email,
                'license_key': license_key,
                'hardware_id': hardware_id,
                'created_at': datetime.now().isoformat()
            }
            print("2. تم إنشاء بيانات الترخيص")

            # تشفير البيانات
            print("3. تشفير البيانات...")
            encrypted_data = self.cipher_suite.encrypt(json.dumps(license_data).encode())
            print("4. تم تشفير البيانات")

            # إنشاء اسم الملف
            print("5. إنشاء اسم الملف...")
            file_name = f"{hashlib.sha256(email.encode()).hexdigest()[:8]}.enc"
            file_path = os.path.join(LICENSES_DIR, file_name)
            print(f"6. مسار الملف: {file_path}")

            # التأكد من وجود المجلد
            print("7. التحقق من وجود المجلد...")
            os.makedirs(LICENSES_DIR, exist_ok=True)

            # حفظ الملف المشفر
            print("8. حفظ الملف المشفر...")
            with open(file_path, 'wb') as f:
                f.write(encrypted_data)
            print("9. تم حفظ الملف بنجاح")

            return file_path

        except Exception as e:
            print(f"خطأ في إنشاء ملف الترخيص: {e}")
            return None

    @staticmethod
    def read_license_file(encrypted_data: str) -> Optional[dict]:
        """قراءة وفك تشفير ملف الترخيص"""
        try:
            # إنشاء Fernet cipher باستخدام المفتاح العام
            cipher_suite = Fernet(encryption_key)
            
            # فك تشفير البيانات
            decrypted_data = cipher_suite.decrypt(encrypted_data)
            
            # تحويل البيانات إلى قاموس
            return json.loads(decrypted_data.decode())

        except Exception as e:
            print(f"خطأ في قراءة ملف الترخيص: {e}")
            return None

# إنشاء مثيل من مدير التراخيص
license_manager = RemoteLicenseManager()

# إنشاء مثيل من مدير ملفات التراخيص
license_file_manager = LicenseFileManager()


@app.post("/generate-license")
async def generate_license(request: Request):
    try:
        print("1. بدء استلام البيانات...")
        data = await request.json()
        email = data.get("email")
        client_id = data.get("client_id")
        hardware_id = data.get("hardware_id")
        duration = data.get("duration", 365)
        
        print(f"2. البيانات المستلمة: email={email}, client_id={client_id}, hardware_id={hardware_id}")
        
        if not all([email, client_id, hardware_id]):
            print("3. خطأ: بيانات مفقودة")
            return JSONResponse(
                {"error": "جميع البيانات مطلوبة"},
                status_code=400
            )

        print("4. إنشاء الترخيص في قاعدة البيانات...")
        # إنشاء الترخيص في قاعدة البيانات
        license_key = license_manager.add_license(email, client_id, hardware_id, duration)
        if not license_key:
            print("5. خطأ: فشل في إنشاء الترخيص")
            return JSONResponse(
                {"error": "فشل في إنشاء الترخيص"},
                status_code=400
            )

        print("6. إنشاء ملف الترخيص المشفر...")
        # إنشاء ملف الترخيص المشفر
        license_file_path = license_file_manager.create_license_file(email, license_key, hardware_id)
        print(f"7. مسار ملف الترخيص: {license_file_path}")
        
        if not license_file_path:
            print("8. خطأ: فشل في إنشاء ملف الترخيص")
            return JSONResponse(
                {"error": "فشل في إنشاء ملف الترخيص"},
                status_code=500
            )

        print("9. إرجاع ملف الترخيص...")
        # إرجاع الملف للتحميل
        return FileResponse(
            license_file_path,
            media_type='application/octet-stream',
            filename='license.enc'
        )

    except Exception as e:
        print(f"خطأ غير متوقع: {str(e)}")
        return JSONResponse(
            {"error": str(e)},
            status_code=500
        )
@app.post("/verify-license")
async def verify_license(request: Request):
    try:
        # استلام البيانات من الطلب
        try:
            data = await request.json()
        except json.JSONDecodeError:
            return JSONResponse({
                "valid": False,
                "message": "البيانات المرسلة غير صالحة"
            })

        license_key = data.get('license_key')
        hardware_id = data.get('hardware_id')
        
        if not license_key or not hardware_id:
            return JSONResponse({
                "valid": False,
                "message": "يجب توفير مفتاح الترخيص ورقم الجهاز"
            })

        # التحقق من الترخيص
        try:
            is_valid, message = license_manager.verify_license(license_key, hardware_id)
        except Exception as e:
            print(f"خطأ في التحقق من الترخيص: {str(e)}")
            return JSONResponse({
                "valid": False,
                "message": "حدث خطأ أثناء التحقق من الترخيص"
            })

        if not is_valid:
            return JSONResponse({
                "valid": False,
                "message": message
            })

        return JSONResponse({
            "valid": True,
            "message": message
        })
    except Exception as e:
        print(f"خطأ غير متوقع: {str(e)}")
        return JSONResponse({
            "valid": False,
            "message": "حدث خطأ غير متوقع"
        })

@app.get("/")
async def home(request: Request):
    # عرض صفحة index.html مع تمرير كائن الطلب
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/process_query")
async def process_query(request: Request):
    try:
        data = await request.json()
        query = data.get('query', '')
        api_key = data.get('api_key', '')
        print(data)
        
        if not query:
            return JSONResponse({
                'status': 'error',
                'message': 'لم يتم توفير استعلام'
            })

        if not api_key:
            return JSONResponse({
                'status': 'error',
                'message': 'لم يتم توفير مفتاح API'
            })

        nl_to_sql = AgenticNLToSQL(
            connection_string=CONFIG_DB,
            openai_api_key=api_key
        )
        
        # معالجة الاستعلام باستخدام الكلاس
        response = nl_to_sql.process_natural_query(query)
        
        # التحقق من وجود استعلام SQL
        if not response.get('sql_query'):
            return JSONResponse({
                'status': 'error',
                'message': 'لم يتم إنشاء استعلام SQL'
            })

        del nl_to_sql
        return JSONResponse({
            'status': 'success',
            'sql_query': response['sql_query'],
            'table_name': response['table_name'],
            'table_name_ar': response['table_name_ar']
        })

    except Exception as e:
        return JSONResponse({
            'status': 'error',
            'message': f'حدث خطأ: {str(e)}'
        })

@app.post("/process_audio")
async def process_audio(request: Request, audio: UploadFile = File(...)):
    print("\n=== بداية معالجة الصوت ===")
    print(f"نوع الطلب: {request.method}")
    
    try:
        api_key = request.headers.get('X-API-Key', '')
        
        if not api_key:
            return JSONResponse({
                'status': 'error',
                'message': 'لم يتم توفير مفتاح API'
            })

        print(f"\nمعلومات الملف الوتي:")
        print(f"اسم الملف: {audio.filename}")
        print(f"نوع المحتوى: {audio.content_type}")
        
        # تصحيح طريقة قراءة وكتابة الملف
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_audio:
            # قراءة محتوى الملف بالكامل
            content = await audio.read()
            # كتابة المحتى إلى الملف المؤقت
            temp_audio.write(content)
            temp_audio_path = temp_audio.name
            print(f"\nتم حفظ الملف المؤقت في: {temp_audio_path}")

        try:
            print("\nبدء تحويل الصوت إلى نص...")
            client = OpenAI(
                api_key=api_key
            )

            with open(temp_audio_path, "rb") as audio_file:
                transcription = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="ar"
                )
                
            extracted_text = transcription.text
            print(f"النص المستخرج: {extracted_text}")

            if not extracted_text:
                return JSONResponse({
                    'status': 'error',
                    'message': 'لم يتم توفير استعلام'
                })

            nl_to_sql = AgenticNLToSQL(
                connection_string=CONFIG_DB,
                openai_api_key=api_key
            )

            # معالجة الاستعلام باستخدام الكلاس
            response = nl_to_sql.process_natural_query(extracted_text)
            
            # التحقق من وجود استعلام SQL
            if not response.get('sql_query'):
                return JSONResponse({
                    'status': 'error',
                    'message': 'لم يتم إنشاء استعلام SQL'
                })

            del nl_to_sql
            return JSONResponse({
                'status': 'success',
                'sql_query': response['sql_query'],
                'table_name': response['table_name'],
                'table_name_ar': response['table_name_ar'],
                'database_schemas': response['database_schemas'],
                'user': str(extracted_text)
            })

        except Exception as e:
            print(f"خطأ في معالجة الصوت: {str(e)}")
            return JSONResponse({
                'status': 'error',
                'message': f'خطأ في معالجة الصوت: {str(e)}'
            })

    except Exception as e:
        return JSONResponse({
            'status': 'error',
            'message': f'حدث خطأ: {str(e)}'
        })
    

@app.get("/get-encrypted-schema")
async def get_encrypted_schema():
    try:
        # قراءة ملف المخطط
        with open("database_schemas.json", "r", encoding='utf-8') as f:
            schema_data = json.load(f)
        
        # تحويل البيانات إلى نص
        schema_str = json.dumps(schema_data)
        
        # مفتاح التشفير - يجب أن يكون نفس المفتاح المستخدم في جهة العميل
        secret = b'cw_0x689RpI-jtRR7oE8h_eQsKImvJapLeSbXpwF4e4='
        
        # إنشاء كائن Fernet مع نفس الإصدار المستخدم في العميل
        fernet = Fernet(secret)
        
        # تشفير البيانات
        encrypted_data = fernet.encrypt(schema_str.encode())
        
        # إرجاع البيانات المشفرة كما هي دون تحويل إضافي
        return JSONResponse({
            "encrypted_data": encrypted_data.decode('utf-8')
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
