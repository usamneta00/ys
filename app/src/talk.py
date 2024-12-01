import oracledb
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import os
from openai import OpenAI, APIConnectionError, APIError
import json
from config import TABLES_AR,TABLES_EN,OWNER,SCHEMA_FILE
from query_where_processor import QueryWhereProcessor
from table_context_processor import TableContextProcessor
import re

class AgenticNLToSQL:
    def __init__(self, connection_string, openai_api_key):
        try:
            self.connection = oracledb.connect(connection_string)
            self.openai_client = OpenAI(api_key=openai_api_key)

            # تحديد المسار الكامل للملف
            current_dir = os.path.dirname(os.path.abspath(__file__))
            schema_file_path = os.path.join(current_dir, SCHEMA_FILE)
            # قراءة ملف database_schemas
            with open(schema_file_path, 'r', encoding='utf-8') as f:
                schemas = json.load(f)
                # إضافة OWNER لكل جدول
                self.database_schemas = schemas
             # إنشاء معالج سياق الجداول
            self.table_context_processor = TableContextProcessor(database_schemas=self.database_schemas,openai_api_key=openai_api_key)
            
        
            # تهيئة OpenAI فقط
            self.openai_client = OpenAI(api_key=openai_api_key)
            
        except Exception as e:
            print(f"خطأ في الاتصال بقاعدة البيانات: {str(e)}")
            raise
        
    def generate_sql(self, natural_query):
        """توليد استعلام SQL من السؤال الطبيعي"""
        print("\nجاري إنشاء قالب ديناميكي للسؤال:", natural_query)
        try:
            template_data = self.generate_dynamic_template(natural_query)
            if not template_data:
                print("فشل في إنشاء قالب ديناميكي")
                return None, "لم أتمكن من فهم السؤال بشكل جيد. يرجى إعادة صياغة السؤال."
        except Exception as e:
            raise Exception(str(e))


        try:
            # معالجة المعلمات باستخدام الكلاس الجديد
            query_processor = QueryWhereProcessor(connection=self.connection)
            params = query_processor.process_parameters(template_data, natural_query)         
            
            # تحضير الاستعلام النهائي
            sql_query = template_data['template']
            
            # استبدال المعلمات في الاستعلام فقط إذا كانت موجودة
            for param_name, param_value in params.items():
                placeholder = f"{param_name}"
                if placeholder in sql_query:  # تحقق من وجود المعلمة في الاستعلام
                    if isinstance(param_value, str):  # للمعلمات النصية
                        sql_query = sql_query.replace(placeholder, f"'{param_value}'")
                    else:  # للمعلمات الرقمية
                        sql_query = sql_query.replace(placeholder, str(param_value))
            
            print("\nالمعلمات المستخدمة:", params)
            print("\nالاستعلام النهائي:", sql_query)
            
            return sql_query, 'dynamic'
        
            
        except Exception as e:
            print(f"\nخطأ في توليد الاستعلام: {str(e)}")
            raise
            #return f"حدث خطأ في معالجة الاستعلام: {str(e)}"

    def process_natural_query(self, natural_query):
        try:
            sql_query, template_type = self.generate_sql(natural_query)
        except Exception as e:
            raise
        
        if sql_query:
            print(f"نوع الاستعلام: {template_type}")
            print(f"الاستعلام SQL: {sql_query}")
            
            # استخراج اسم الجدول من الاستعلام SQL
            table_name = None
            is_english = len([c for c in natural_query.lower() if ord('a') <= ord(c) <= ord('z')]) > len([c for c in natural_query if '\u0600' <= c <= '\u06FF'])
                    
            for table in TABLES_EN.keys():
                    if table.upper() in sql_query.upper():
                        table_name = table
                        break

            return {
                'sql_query': sql_query,
                'template_type': template_type,
                'table_name': table_name,
                'table_name_ar': TABLES_AR.get(table_name, table_name) if table_name and not is_english else TABLES_EN.get(table_name, table_name) if table_name else "Unknown Table" if is_english else "جدول غير معروف",
                'database_schemas': self.database_schemas  # إضافة مخططات قاعدة البيانات
            }
        return {
            'sql_query': None,
            'template_type': None,
            'table_name': None,
            'table_name_ar': None,
        }

    def _generate_alternative_queries(self, original_query,table_contexts):
        try:
            # التحقق من لغة السؤال الأصلي
            is_english = len([c for c in original_query.lower() if ord('a') <= ord(c) <= ord('z')]) > len([c for c in original_query if '\u0600' <= c <= '\u06FF'])
            
            if is_english:
                prompt = f"""
                Suggest 3 different phrasings for the following question while maintaining the same meaning.
                The phrasings should use accounting terminology:
                
                Original question: {original_query}
                
                Output only the alternative phrasings, one per line.

                Context:
                I found that your question relates to {table_contexts}.
                Based on this context, here are some related terms and keywords:

                Keywords: {[keyword for keyword in table_contexts.get('keywords', [])]}

                Please use these terms to phrase alternative questions that fit the specified context.
                
                Remove the question mark from alternative questions.
                """
            else:
                prompt = f"""
                اقترح 3 صيغ مختلفة للسؤال التالي مع الحفاظ على نفس المعنى. 
                يجب أن تكون الصيغ باللغة العربية وتستخدم مصطلحات محاسبية:
                
                السؤال الأصلي: {original_query}
                
                قم بإخراج الصيغ البديلة فقط، كل صيغة في سطر منفصل.

                السياق: 
                لقد وجدت أن سؤالك يتعلق بـ {table_contexts}. 
                بناءً على هذا السياق، إليك بعض المصطلحات والكلمات المفتاحية المرتبطة:

                الكلمات المفتاحية: {[keyword for keyword in table_contexts.get('keywords', [])]}

                يرجى استخدام هذه المصطلحات لصياغة أسئلة بديلة تتناسب مع السياق المحدد.
                
                احذف علامة الاستفهام من الأسئلة البديلة.
                """

            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a specialized assistant in accounting terminology" if is_english else "أنت مساعد متخصص في المصطلحات المحاسبية"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=150
            )

            alternative_queries = response.choices[0].message.content.strip().split('\n')
            return [query.strip() for query in alternative_queries if query.strip()]

        except Exception as e:
            print(f"Error generating alternative questions: {str(e)}" if is_english else f"خطأ في توليد الأسئلة البدلة: {str(e)}")
            return []

    
    def levenshtein_distance(self, s1, s2):
        """حساب مسافة Levenshtein بين سلسلتين"""
        if len(s1) < len(s2):
            return self.levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def preprocess_columns(self, natural_query, table_schema):
        """تحليل مسبق للأعمدة باستخدام TF-IDF وحساب التشابه"""
        try:
            # إضافة فحص أولي للنص المدخل
            if not natural_query.strip():
                return []
                
            # تحديد اللغة
            english_chars = len([c for c in natural_query.lower() if ord('a') <= ord(c) <= ord('z')])
            arabic_chars = len([c for c in natural_query if '\u0600' <= c <= '\u06FF'])
            
            # تحضير النصوص للتحليل
            texts = []
            columns_data = []
            
            # إضافة نص ثابت لضمان وجود محتوى
            base_content = "content محتوى abc 123 اب ت"
            
            # معالجة النص المدخل
            normalized_query = self.normalize_arabic_text(natural_query.lower())
            texts.append(f"{normalized_query} {base_content}")
            
            # تجميع نصوص الأعمدة
            for col_name, col_info in table_schema['columns'].items():
                description = str(col_info.get('description', ''))
                caption = str(col_info.get('caption_det', ''))
                
                # إضافة المحتوى الثابت للنصوص
                description = f"{description} {base_content}"
                caption = f"{caption} {base_content}"
                
                # تطبيع النصوص
                normalized_desc = self.normalize_arabic_text(description.lower())
                normalized_caption = self.normalize_arabic_text(caption.lower())
                
                texts.append(normalized_desc)
                texts.append(normalized_caption)
                
                columns_data.append({
                    'name': col_name,
                    'description': description,
                    'caption': caption,
                    'normalized_desc': normalized_desc,
                    'normalized_caption': normalized_caption
                })

            # التأكد من وجود محتوى صالح
            if not any(text.strip() for text in texts):
                texts.append(base_content)

            # حساب TF-IDF
            vectorizer = TfidfVectorizer(ngram_range=(1, 3), analyzer='char_wb', min_df=1)
            tfidf_matrix = vectorizer.fit_transform(texts)
            
            # حساب التشابه
            similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])
            
            # تجمي النتائج مع مراعاة التطابق الجزئي
            relevant_columns = []
            for idx, col_data in enumerate(columns_data):
                # حساب درجة التشابه لكل جزء من النص
                query_parts = normalized_query.split()
                desc_parts = col_data['normalized_desc'].split()
                caption_parts = col_data['normalized_caption'].split()
                
                max_desc_score = 0
                max_caption_score = 0
                
                for query_part in query_parts:
                    # حساب أعلى درجة تشابه مع أجزاء الوصف
                    for desc_part in desc_parts:
                        similarity = self.calculate_partial_similarity(query_part, desc_part)
                        max_desc_score = max(max_desc_score, similarity)
                    
                    # حساب أعلى درجة تشابه مع أزاء العنوان
                    for caption_part in caption_parts:
                        similarity = self.calculate_partial_similarity(query_part, caption_part)
                        max_caption_score = max(max_caption_score, similarity)
                
                final_score = (max_desc_score * 0.6) + (max_caption_score * 0.4)
                
                if final_score > 0.2:  # عتبة التصفية
                    relevant_columns.append({
                        'name': col_data['name'],
                        'score': final_score,
                        'description': col_data['description'],
                        'caption': col_data['caption']
                    })

            # تحليل نمط السؤال
            def analyze_query_pattern(query):
                query_parts = query.split()
                specific_patterns = [
                    'اظهر', 'show', 'عرض', 'display', 'اعرض', 'view',
                    'حيث', 'where', 'بحيث', 'such that', 'مع', 'with',
                    'و', 'and', 'يظهر', 'shows', 'يتضمن', 'includes',
                    'يشمل', 'contains', 'تظهر', 'appears', 'تتضمن', 'includes',
                    'تشمل', 'contains'
                ]
                return any(pattern in query_parts for pattern in specific_patterns)

            # ترتيب الأعمدة حسب درجة التشابه
            relevant_columns.sort(key=lambda x: x['score'], reverse=True)
            
            # تحليل نمط السؤال
            is_specific_query = analyze_query_pattern(natural_query)
            
            # إذا كان السؤال يطلب معلومات محددة ودرجة التشابه عالية
            if is_specific_query and relevant_columns:  # تم إزالة الفحص على relevant_columns[0]
                # إرجاع الأعمدة ذات الصلة فقط
                return relevant_columns[:10]
            else:
                # إرجاع جميع الأعمدة في الحالات الأخرى
                all_columns = []
                for col_name, col_info in table_schema['columns'].items():
                    all_columns.append({
                        'name': col_name,
                        'score': 0.1,
                        'description': str(col_info.get('description', '')),
                        'caption': str(col_info.get('caption_det', ''))
                    })
                return all_columns

        except Exception as e:
            print(f"خطأ في التحليل المسبق: {str(e)}")
            return []


    def generate_dynamic_template(self, natural_query):
        """إنشاء قالب ديناميكي باستخدام OpenAI"""
        try:
            # تحديد الجدول المناسب
            table_name, table_schema, table_contexts = self.table_context_processor.get_table_context(natural_query)

            # إضافة فحص للتأكد من وجود الجدول
            if table_name not in self.database_schemas:
                print(f"الجدول {table_name} غير موجود في database_schemas")
                raise Exception("الصيغ البديلة: "+str(self._generate_alternative_queries(natural_query,table_contexts)))
                
            # التأكد من أن table_schema ليس None
            if not table_schema:
                print("table_schema فارغ")
                return None

            # استخدام preprocess_columns للحصول على الأعمدة ذات الصلة
            relevant_columns = self.preprocess_columns(natural_query, table_schema)
            
            # طباعة معلومات الأعمدة ذات الصلة
            print("\nالأعمدة ذات الصلة بالسؤال:")
            for idx, col in enumerate(relevant_columns[:3], 1):
                print(f"\n{idx}. العمود: {col['name']}")
                print(f"   الوصف: {col['description']}")
                print(f"   درجة التطابق: {col['score']:.2f}")

            # استخدام أفضل 3 أعمدة متطابقة
            best_matches = relevant_columns[:5] if relevant_columns else []
            if best_matches:
                print("\nالأعمدة الأكثر تطابقاً:")
                for idx, match in enumerate(best_matches, 1):
                    print(f"{idx}. {match['name']} (درجة التطابق: {match['score']:.2f})")

            # تحضير السياق مع معلومات الأعمدة
            context = f"""
            معلومات جدول {table_name}:
            {json.dumps(table_schema, ensure_ascii=False, indent=2)}
            
            مطلوب: إنشاء قالب SQL يناسب السؤال التالي: {natural_query}
            
            أفضل الأعمدة المتطابقة:
            {json.dumps([{
                'name': match['name'],
                'description': match['description'],
                'score': match['score']
            } for match in best_matches], ensure_ascii=False, indent=2)}
            
            قواعد مهمة:
            1. استخدم فقط الأعمدة التالية (لا تستخدم أي أعمدة أخرى):
            {', '.join([f"{col} ({info.get('caption_det_en', info.get('caption_det', ''))})" for col, info in table_schema['columns'].items()])}
            
            2. لا تقم بإنشاء أو اختراع أي أعمدة جديدة.
            3. استخدم فقط الأعمدة المذكورة أعلاه في استعلام SQL.
            4. إذا كان السؤال يتطلب عموداً غير موجود، استخدم أقرب عمود متاح من القائمة أعلاه.
            5. إذا كان السؤال يحتوي على كلمات مثل "الجميع" أو "جميع" أو "كل" أو "الكل"، لا تضف FETCH FIRST
            6. في الحالات الأخرى، أضف FETCH FIRST :limit ROWS ONLY
            7. عند السؤال عن أسماء تبدأ بحرف معين، استخدم LIKE مع :name_prefix
            8. عند السؤال عن أسماء تنتهي بحرف معين، استخدم LIKE مع :name_suffix
            9. عند البحث عن اسم العميل، استخدم LIKE مع :CUSTOMER_NAME
            10. عند البحث عن رمز الصنف، استخدم LIKE مع :item_code

            يجب أن يكون القالب بالتنسيق التالي:
            {{
                "template": "استعلام SQL",
                "parameters": ["قائمة المعلمات المستخدمة"],
                "questions": ["السؤال الأصلي"],
                "best_matches": {json.dumps(best_matches, ensure_ascii=False)}
            }}
            """

            # تحديد ما إذا كان السؤال باللغة الإنجليزية
            is_english = len([c for c in natural_query if ord('a') <= ord(c.lower()) <= ord('z')]) > len([c for c in natural_query if '\u0600' <= c <= '\u06FF'])

            # تحضير السياق بناءً على اللغة
            if is_english:
                context = f"""
                Table {table_name} information:
                {json.dumps(table_schema, ensure_ascii=False, indent=2)}
                
                Required: Create an SQL template that matches the following question: {natural_query}
                
                Best matching columns:
                {json.dumps([{
                    'name': match['name'],
                    'description': match['description'],
                    'score': match['score']
                } for match in best_matches], ensure_ascii=False, indent=2)}
                
                Important rules:
                1. Use only the following columns (do not use any other columns):
                {', '.join([f"{col} ({info.get('caption_det_en', info.get('caption_det', ''))})" for col, info in table_schema['columns'].items()])}
                
                2. Do not create or invent any new columns.
                3. Use only the columns mentioned above in the SQL query.
                4. If the question requires a column that doesn't exist, use the closest available column from the list above.
                5. If the question contains words like "all" or "every", do not add FETCH FIRST
                6. In other cases, add FETCH FIRST :limit ROWS ONLY
                7. When asking about names starting with a certain letter, use LIKE with :name_prefix
                8. When asking about names ending with a certain letter, use LIKE with :name_suffix
                9. When searching for customer name, use LIKE with :CUSTOMER_NAME
                10. When searching for item code, use LIKE with :item_code

                The template should be in the following format:
                {{
                    "template": "SQL query",
                    "parameters": ["list of used parameters"],
                    "questions": ["original question"],
                    "best_matches": {json.dumps(best_matches, ensure_ascii=False)}
                }}
                """
            
            # تحديد محتوى رسالة النظام بناءً على اللغة
            system_content = """
            You are a specialist in converting English questions to SQL queries.
            - Use the column name specified in the context
            - Make sure to use the correct column name in the query
            """ if is_english else """
            أنت مساعد متخصص في تحويل الأسئلة باللغة العربية إلى استعلامات SQL.
            - استخدم اسم العمود المحدد في السياق
            - تأكد من استخدام الاسم الصحيح للعمود في الاستعلام
            """

            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": context}
                ],
                temperature=0.1
            )

            template_str = response.choices[0].message.content
            template_str = template_str[template_str.find('{'):template_str.rfind('}')+1]
            template_data = json.loads(template_str)

            #print(f"\nالقالب المستخرج للجدول {table_name}:", json.dumps(template_data, ensure_ascii=False, indent=2))

            return template_data
        except APIConnectionError as e:
            raise APIConnectionError(
                message="عذراً، حدث خطأ في الاتصال بالخدمة. يرجى التحقق من اتصال الإنترنت والمحاولة مرة أخرى.",
                body={"error": str(e)},
                request=None
            )
        except APIError as e:
            raise APIError(
                message="عذراً، يرجى التأكد من صحة مفتاح API الخاص بك. إذا كان المفتاح صحيحاً، يمكنك المحاولة مرة أخرى لاحقاً.",
                body={"error": str(e)},
                request=None
            )
        except Exception as e:
            raise Exception(str(e))


    def normalize_arabic_text(self, text):
        """تطبيع النص العربي وإزالة التشكيل والأحرف الخاصة"""
        try:
            # تحويل النص إلى سلسلة نصية
            text = str(text)
            
            # قائمة الأحرف العربية للتشكيل
            arabic_diacritics = re.compile("""
                ّ    | # Shadda
                َ    | # Fatha
                ً    | # Tanwin Fath
                ُ    | # Damma
                ٌ    | # Tanwin Damm
                ِ    | # Kasra
                ٍ    | # Tanwin Kasr
                ْ    | # Sukun
                ـ     # Tatweel/Kashida
            """, re.VERBOSE)
            
            # إزالة التشكيل
            text = re.sub(arabic_diacritics, '', text)
            
            # استبدال الألف المقصورة والهمزات
            replacements = {
                'ى': 'ي',
                'أ': 'ا',
                'إ': 'ا',
                'آ': 'ا',
                'ة': 'ه',
                '\u200f': '',  # علامة RTL
                '\u200e': '',  # علامة LTR
            }
            
            for old, new in replacements.items():
                text = text.replace(old, new)
            
            # إزالة الأحرف غير العربية والأرقام
            text = re.sub(r'[^\u0600-\u06FF\s]', ' ', text)
            
            # إزالة المسافات المتعددة
            text = re.sub(r'\s+', ' ', text)
            
            return text.strip()
            
        except Exception as e:
            print(f"خطأ في تطبيع النص العربي: {str(e)}")
            return text

    def calculate_partial_similarity(self, text1, text2):
        """حساب التشابه الجزئي بين نصين باستخدام مسافة Levenshtein"""
        try:
            # تطبيع النصوص
            text1 = self.normalize_arabic_text(str(text1).lower())
            text2 = self.normalize_arabic_text(str(text2).lower())
            
            # حساب مسافة Levenshtein
            distance = self.levenshtein_distance(text1, text2)
            
            # حساب درجة التشابه (1 = تطابق تام، 0 = لا يوجد تشابه)
            max_length = max(len(text1), len(text2))
            if max_length == 0:
                return 0
                
            similarity = 1 - (distance / max_length)
            return similarity
            
        except Exception as e:
            print(f"خطأ في حساب التشابه الجزئي: {str(e)}")
            return 0

