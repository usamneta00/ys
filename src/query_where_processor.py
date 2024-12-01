import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from config import OWNER

class QueryWhereProcessor:
    def __init__(self, connection):
        self.connection = connection
        self.owner = OWNER.strip('"\'')
        self.params = {}

    def process_parameters(self, template_data, natural_query):
        """معالجة جميع المعلمات المطلوبة في القالب"""
        try:
            # تحديث القيم من السؤال
            self._handle_name_prefix(template_data, natural_query)
            self._handle_name_suffix(template_data, natural_query)
            self._handle_limit(template_data, natural_query)
            self._handle_customer_name(template_data, natural_query)
            self._handle_item_code(template_data, natural_query)
            
            return self.params
            
        except Exception as e:
            print(f"خطأ في معالجة المعلمات: {str(e)}")
            raise

    def _handle_name_prefix(self, template_data, natural_query):
        # تحديث القيم من السؤال
        if ':name_prefix' in template_data['parameters']:
            print("\nجاري البحث عن بادئة الاسم...")
            extracted_prefix = self.extract_name_prefix(natural_query)
            if extracted_prefix:
                self.params[':name_prefix'] = f"{extracted_prefix}%"
                print(f"تم تحديث name_prefix إلى: {self.params[':name_prefix']}")
            else:
                print("لم يتم العثور على بادئة")

    def _handle_name_suffix(self, template_data, natural_query):
        if ':name_suffix' in template_data.get('parameters', []):
            print("\nجاري البح عن لاحقة الاسم...")
            extracted_suffix = self.extract_name_suffix(natural_query)
            if extracted_suffix:
                self.params[':name_suffix'] = f"%{extracted_suffix}"
                print(f"تم تحديث name_suffix إلى: {self.params[':name_suffix']}")
            else:
                print("لم يتم العثور على لاحقة")

    def _handle_limit(self, template_data, natural_query):
        if ':limit' in template_data['parameters']:
            extracted_limit = self.extract_limit(natural_query)
            if extracted_limit:
                self.params[':limit'] = extracted_limit

    def _handle_customer_name(self, template_data, natural_query):
        # معالجة customer_name
        if ':CUSTOMER_NAME' in template_data['parameters']:
            print("\nجاري البحث عن اسم العميل...")
            extracted_name = self.extract_customer_name(natural_query)
            if extracted_name:
                self.params[':CUSTOMER_NAME'] = f"%{extracted_name}%"
                print(f"تم تحديث CUSTOMER_NAME إلى: {self.params[':CUSTOMER_NAME']}")
            else:
                print("لم يتم العثور على اسم العميل")

    def _handle_item_code(self, template_data, natural_query):
        if ':item_code' in template_data['parameters']:
            print("\nجاري البحث عن رمز الصنف...")
            extracted_code = self.extract_item_code(natural_query)
            if extracted_code:
                self.params[':item_code'] =  f"%{extracted_code}%"
                print(f"تم تحديث item_code إلى: {self.params[':item_code']}")
            else:
                print("لم يتم العثور على رمز الصنف")

    
    def extract_limit(self, natural_query):
        # قاموس تحويل الأرقام المكتوبة بالحروف إلى أرقام
        number_words = {
            'واحد': '1', 'اثنين': '2', 'ثلاثة': '3', 'اربعة': '4', 'خمسة': '5',
            'ستة': '6', 'سبعة': '7', 'ثمانية': '8', 'تسعة': '9', 'عشرة': '10',
            'احدى عشر': '11', 'اثنى عشر': '12', 'ثلاثة عشر': '13', 'اربعة عشر': '14',
            'خمسة عشر': '15', 'ستة عشر': '16', 'سبعة عشر': '17', 'ثمانية عشر': '18',
            'تسعة عشر': '19', 'عشرين': '20'
        }
        
        # استبدال الأرقام المكتوبة بالحروف بأرقام رقمية
        query = natural_query.replace('أ', 'ا').replace('إ', 'ا')  # توحيد الهمزات
        for word, number in number_words.items():
            query = query.replace(word, number)
            
        # تحسين التعبير المنتظم ليشمل المزيد من الحالات
        patterns = [
            # النمط الأصلي
            r'(?:افضل|اكبر|اكثر|اقل|اعلى|ادنى|اقصى|اول|اخر)\s*(\d+)',
            # النمط المعكوس (الرقم قبل الكلمة)
            r'(\d+)\s*(?:افضل|اكبر|اكثر|اقل|اعلى|ادنى|اقصى|اول|اخر)',
            # نمط "اعطني X" أو "أريد X"
            r'(?:اعطني|اريد|اريد|اظهر|اظهر)\s*(?:افضل|اكبر|اكثر|اقل|اعلى|ادنى|اقصى)?\s*(\d+)',
            # مط "أريد أفضل X"
            r'(?:اريد|اريد)\s+(?:افضل|اكبر|اكثر|اقل|اعلى|ادنى|اقصى)\s*(\d+)',
            # نمط عام للأرقا في السياق
            r'(?:عدد|رقم|كمية|حوالي|تقريبا|قرابة)\s*(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                # التحقق من المجموعات في النمط
                number = match.group(1)
                try:
                    return int(number)
                except ValueError:
                    continue
        
        return 10  # القيمة الافتراضية

    def extract_name_prefix(self, query):
        """استخراج الحرف الذي يبدأ به الاسم من السؤال"""
        try:
            # قائمة الكلمات المفتاحية التي تشير إلى البداية
            start_keywords = [
                'يبدأ ب', 'تبدأ ب', 'يبدا ب', 'تبدا ب',
                'أوله', 'اوله', 'أولها', 'اولها',
                'حرف', 'بحرف'
            ]

            # قاموس تحويل أسماء الحروف إلى الحروف نفسها
            letter_names = {
                'الالف': 'ا', 'الألف': 'ا',
                'الباء': 'ب', 
                'التاء': 'ت',
                'الثاء': 'ث',
                'الجيم': 'ج',
                'الحاء': 'ح',
                'الخاء': 'خ',
                'الدال': 'د',
                'الذال': 'ذ',
                'الراء': 'ر',
                'الزاي': 'ز', 'الزين': 'ز',
                'السين': 'س',
                'الشين': 'ش',
                'الصاد': 'ص',
                'الضاد': 'ض',
                'الطاء': 'ط',
                'الظاء': 'ظ',
                'العين': 'ع',
                'الغين': 'غ',
                'الفاء': 'ف',
                'القاف': 'ق',
                'الكاف': 'ك',
                'اللام': 'ل',
                'الميم': 'م',
                'النون': 'ن',
                'الهاء': 'ه',
                'الواو': 'و',
                'الياء': 'ي'
            }
            
            # تنظيف النص وتوحيد الهمزات
            query = query.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
            print(f"\nالسؤال بعد التنظيف: {query}")
            
            # البحث عن أسماء الحروف في النص
            for letter_name, letter in letter_names.items():
                if letter_name in query:
                    print(f"تم العثور على اسم الحرف: {letter_name} -> {letter}")
                    return letter

            # البحث عن نمط "يبدأ بحرف X" أو "يبدأ ب X"
            for keyword in start_keywords:
                # استخدام r"" للتعبير المنتظم
                pattern = fr"{keyword}\s*([ابتثجحخدذرزسشصضطظعغفقكلمنهوي])"
                match = re.search(pattern, query, re.IGNORECASE)
                #print(f"البحث عن النمط: {pattern}")
                if match:
                    found_letter = match.group(1)
                    print(f"تم العثور على الحرف: {found_letter}")
                    return found_letter
            
            # نمط للبحث عن الحرف في بداية الجملة
            pattern = r'^([ابتثجحخدذرزسشصضطظعغفقكلمنهوي])\s*(?:حرف|بحرف)'
            match = re.search(pattern, query)
            if match:
                found_letter = match.group(1)
                #print(f"تم العثور على الحرف في بداية الجملة: {found_letter}")
                return found_letter

            # نمط إضافي للبحث عن الحرف بعد "ب" مباشرة
            pattern = r'ب([ابتثجحخدذرزسشصضطظعغفقكمنهوي])\b'
            match = re.search(pattern, query)
            if match:
                found_letter = match.group(1)
                #print(f"تم العثور على الحرف (نمط بديل): {found_letter}")
                return found_letter
            
            print("لم يتم العثور على حرف البداية")
            return None
            
        except Exception as e:
            print(f"خطأ في استخراج بادئة الاسم: {str(e)}")
            return None

    def extract_name_suffix(self, query):
        """استخراج الحرف الذي ينتهي به أي كلمة من السؤال"""
        try:
            # قائمة الكلمات المفتاحية التي تشير إلى النهاية
            end_keywords = ['ينتهي', 'ينتهي ب', 'تنتهي ب',
                'آخره', 'اخره', 'آخرها', 'اخرها',
                'نهايته', 'نهايتها'
            ]

            # قاموس أسماء الحروف العربية
            letter_names = {
                'الألف': 'ا', 'الباء': 'ب', 'التاء': 'ت', 'الثاء': 'ث',
                'الجيم': 'ج', 'الحاء': 'ح', 'الخاء': 'خ', 'الدال': 'د',
                'الذال': 'ذ', 'الراء': 'ر', 'الزاي': 'ز', 'السين': 'س',
                'الشين': 'ش', 'الصاد': 'ص', 'الضاد': 'ض', 'الطاء': 'ط',
                'الظاء': 'ظ', 'العين': 'ع', 'الغين': 'غ', 'الفاء': 'ف',
                'القاف': 'ق', 'الكاف': 'ك', 'اللام': 'ل', 'الميم': 'م',
                'النون': 'ن', 'الهاء': 'ه', 'الواو': 'و', 'الياء': 'ي'
            }
            
            # تنظيف النص وتوحيد الهمزات
            query = query.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
            
            # البحث عن أسماء الحروف في النص
            for letter_name, letter in letter_names.items():
                if letter_name in query:
                    print(f"تم العثور على اسم الحرف: {letter_name} -> {letter}")
                    return letter

            # نمط يبحث عن "ينتهي" أو "تنتهي" متبوعة بأي كلمات ث حرف عربي
            pattern = fr"({'|'.join(end_keywords)}).*?(?:بحرف|ب)\s*([ابتثجحخدذرزسشصضطظعغفقكلمنهوي])\s*"
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                found_letter = match.group(2)
                print(f"تم العثور على الحرف: {found_letter}")
                print(f"النص الكامل الذي تم مطابقته: {match.group(0)}")
                return found_letter

            # نمط للبحث عن الحرف في نهاية الجملة
            pattern = r'([ابتثجحخدذرزسشصضطظعغفقكلمنهوي])\s*(?:حرف|بحرف)?\s*$'
            match = re.search(pattern, query)
            if match:
                found_letter = match.group(1)
                print(f"تم العثور على الحرف في نهاية الجملة: {found_letter}")
                return found_letter

            # نمط للبحث عن الحرف بعد كلمة "حرف" مباشرة
            pattern = r'حرف\s+([ابتثجحخدذرزسشصضطظعغفقكلمنهوي])'
            match = re.search(pattern, query)
            if match:
                found_letter = match.group(1)
                print(f"م العثور على الحرف بعد كلمة حرف: {found_letter}")
                return found_letter
            
            print("لم يتم العثور على لاحقة")
            return None
            
        except Exception as e:
            print(f"خطأ في استخراج لاحقة لاسم: {str(e)}")
            return None
    def extract_customer_name(self, query):
        try:
            # استخراج جميع أسماء العملاء من قاعدة البيانات
            schema_name = OWNER.strip('"\'')
            cursor = self.connection.cursor()
            sql = f"""
            SELECT DISTINCT CSTMR_NM 
            FROM {schema_name}.SALES_BILL_MST_AI_VW 
            WHERE CSTMR_NM IS NOT NULL
            """
            cursor.execute(sql)
            customer_names = [row[0] for row in cursor.fetchall()]
            cursor.close()

            # تنظيف السؤال وتوحيد الهمزات
            query = query.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')

            # أولاً: محاولة استخراج الاسم المفرد
            keywords = ['العميل', 'الزبون', 'المستفيد', 'عميل', 'زبون', 'مستفيد', 'صاحب']
            
            # دالة مساعدة لحساب درجة التشابه
            def calculate_similarity(text1, text2):
                text1 = text1.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
                text2 = text2.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
                text1 = text1.replace('ال', '')
                text2 = text2.replace('ال', '')
                
                vectorizer = TfidfVectorizer(analyzer='char_wb', ngram_range=(2, 3))
                try:
                    tfidf_matrix = vectorizer.fit_transform([text1, text2])
                    return cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
                except:
                    return 0

            # استخراج الأسماء المحتملة
            potential_names = []
            
            # استخراج من بعد الكلمات المفتاحية
            for keyword in keywords:
                if keyword in query:
                    parts = query.split(keyword)
                    if len(parts) > 1:
                        potential_name = parts[1].strip()
                        name_parts = potential_name.split()[:3]
                        potential_names.append(' '.join(name_parts))

            # استخراج من بعد اللام
            if 'ل' in query:
                lam_parts = query.split(' ل')
                if len(lam_parts) > 1:
                    potential_name = lam_parts[1].strip()
                    name_parts = potential_name.split()[:3]
                    potential_names.append(' '.join(name_parts))

            # استخراج الاسم المباشر (بدون ل التعريف أو كلمات مفتاحية)
            words = query.split()
            for i in range(len(words)):
                # تجميع كلمتين أو ثلاث متتالية كاسم محتمل
                if i + 1 < len(words):
                    potential_names.append(f"{words[i]} {words[i+1]}")
                if i + 2 < len(words):
                    potential_names.append(f"{words[i]} {words[i+1]} {words[i+2]}")

            print("الأسماء المركبة المحتملة:", potential_names)

            # البحث عن أفضل تطابق
            best_match = None
            highest_similarity = 0

            for db_name in customer_names:
                for potential_name in potential_names:
                    similarity = calculate_similarity(db_name, potential_name)
                    if similarity > highest_similarity and similarity > 0.5:
                        highest_similarity = similarity
                        best_match = db_name

            if best_match:
                print(f"تم العثور على اسم عميل مركب: {best_match} (درجة التشابه: {highest_similarity})")
                return best_match

            # البحث عن الاسم المباشر في النص
            for word in words:
                if len(word) > 3:  # تجنب الكلمات القصيرة
                    # إزالة ل التعريف إذا وجدت
                    if word.startswith('ل'):
                        word = word[1:]
                    for db_name in customer_names:
                        if word in db_name.split():
                            print(f"تم العثور على اسم عميل مباشر: {db_name}")
                            return db_name
                else:  # تجنب الكلمات القصيرة
                    # إزالة ل التعريف إذا وجدت
                    if word.startswith('ل'):
                        word = word[1:]
                    for db_name in customer_names:
                        if word in db_name.split():
                            print(f"تم العثور على اسم عميل مباشر: {db_name}")
                            return word
                        

                    

            print("لم يتم العثور على أي تطابق للاسم...")
            return None

        except Exception as e:
            print(f"خطأ في استخراج اسم العميل: {str(e)}")
            return None

    def extract_item_code(self, query):
        try:
            print("\nجاري البحث عن رمز الصنف...")

            # تنظيف السؤال
            query = query.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
            
            # أنماط مختلفة للبحث عن رمز الصنف
            patterns = [
                r'\b(\d+[-_]\d+)\b',           # مثل: 13-3
                r'\b(\d+\s*[-_]\s*\d+)\b',     # مثل: 13 - 3
                r'صنف\s*(\d+[-_]\d+)',         # مثل: صنف 13-3
                r'رمز\s*(\d+[-_]\d+)',         # مثل: رمز 13-3
                r'كود\s*(\d+[-_]\d+)',         # مثل: كود 13-3
                r'رقم\s*(\d+[-_]\d+)',         # مثل: رقم 13-3
                r'\b([A-Za-z0-9-_]+)\b'        # أي رمز عام
            ]
            # البحث عن أول نمط يعطي نتيجة صحيحة
            for pattern in patterns:
                matches = re.findall(pattern, query)
                print(f"البحث باستخدام النمط {pattern}، النتائج:", matches)
                
                # إذا وجدنا تطابق، نتحقق من أول نتيجة ونعيدها مباشرة
                if len(matches) > 0:
                    clean_code = matches[0].replace(' ', '')
                    if clean_code:
                        print(f"تم العثور على رمز صنف صالح باستخدام النمط: {pattern}")
                        return clean_code

            print("لم يتم العثور على رمز صنف صالح")
            return None

        except Exception as e:
            print(f"خطأ في استخراج رمز الصنف: {str(e)}")
            return None