from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import json

class TableContextProcessor:
    def __init__(self, database_schemas, openai_api_key):
        """تهيئة معالج سياق الجداول"""
        from openai import OpenAI
        
        # تهيئة OpenAI client
        self.openai_client = OpenAI(
            api_key=openai_api_key
        )
        
        # تخزين مخططات قاعدة البيانات
        self.database_schemas = database_schemas
        
        self.table_contexts = {
            'SALES_BILL_MST_AI_VW': {
                'keywords': ['مبيعات', 'فاتورة', 'فواتير', 'فواتير المبيعات', 'المبيعات',
                'مبيعات', 'فاتورة', 'فواتير',
                'مبيعات', 'فاتورة', 'فواتير',
                'فاتورة رئيسية', 'فواتير رئيسية', 'رأس الفاتورة', 'رؤوس الفواتير',
                'مبيعات رئيسية', 'مبيعات اجمالية', 'فواتير مبيعات رئيسية', 'فواتير مبيعات اجمالية',
                'اجمالي المبيعات', 'اجماليات المبيعات', 'رئيسي المبيعات', 'رئيسيات المبيعات',
                'مجاميع المبيعات', 'مجموع المبيعات', 'ملخص المبيعات', 'ملخصات المبيعات',
                'رأس فاتورة المبيعا', 'رؤوس فواتير المبيعات', 'معلومات رئيسية للمبيعات',
                'بيانات رئيسية للفواتير', 'معلومات اساسية للمبيعات', 'بيانات اساسية للفواتير',
                'ملخص فواتير المبيعات', 'اجماليات فواتير المبيعات', 'مجاميع فواتير المبيعات',
                'فواتير العملاء', 'مبيعات العملاء',
                'فواتير الزبائن', 'مبيعات الزبائن', 
                'فواتير المشترين', 'مبيعات المشترين', 
                'فواتير المستهلكين', 'مبيعات المستهلكين',
                'عميل', 'عملاء', 'مبيعات عميل', 'مبيعات عملاء',
                'فاتورة عميل', 'فواتير عملاء', 'فواتير عميل', 'فاتورة عملاء',
                'مبيعات العميل', 'مبيعات العملاء', 'فواتير العميل', 'فواتير العملاء'
                ],
                'negative': ['مردود', 'مرتجع', 'استرجاع', 'تحليل', 'تحليلي'],
                'context': 'فواتير المبيعات الرئيسية',
                'description': ' يحتوي على بيانات حول معاملات المبيعات، بما في ذلك معلومات عالية المستوى حول كل عملية بيع على مستوى الفاتورة أو المعاملة.'
                },
            'SALES_BILL_ANALYSIS_AI_VW': {
                'keywords': ['المبيعات التحليلية','تحليل المبيعات', 'تحليلي المبيعات', 'تفاصيل المبيعات', 'المبيعات تحليل',                
                'تحليل المبيعات', 'المبيعات تحليل', 'حليلي المبيعات', 'المبيعات تحليلي',
                'تحليل فواتير المبيعات', 'المبيعات فواتير تحليل', 'تحليلي فواتير المبيعات', 'المبيعات فواتير تحليلي',
                'تفاصيل المبيعات', 'المبيعات تفاصيل', 'تفاصيل الفواتير', 'الفواتير تفاصيل',
                'تفصيلي المبيعات', 'المبيعات تفصيلي', 'تفصيلي الفواتير', 'الفواتير تفصيلي',
                'احصائيات المبيعات', 'المبيعات احصائيات', 'احصائيات الفواتير', 'الفواتير احصائيات',
                'تقارير المبيعات', 'المبيعات تقارير', 'تقارير الفواتير', 'الفواتير تقارير',
                'تحليلة المبيعات', 'المبيعات تحليلة', 'تحليلية المبيعات', 'المبيعات تحليلية','المبيعات التحليلية',
                'تحليلة فواتير المبيعات', 'المبيعات فواتير تحليلة', 'تحليلية فواتير المبيعات', 'المبيعات فواتير تحليلية',
                'تفاصيل كاملة للمبيعات', 'تفاصيل كاملة للفواتير', 'تحليل كامل للمبيعات', 'تحليل كامل للفواتير',
                'تحليل شامل للمبيعات', 'تحليل شامل للفواتير', 'تفاصيل شاملة للمبيعات', 'تفاصيل شاملة للفواتير',
                'تحليل مفصل للمبيعات', 'تحليل مفصل للفواتير', 'تفاصيل مفصلة للمبيعات', 'تفاصيل مفصلة للفواتير',
                'تحليل مبيعات العملاء', 'تفاصيل مبيعات العملاء', 'تحليلي مبيعات العملاء',
                'العملاء مبيعات تحليل', 'العملاء مبيعات تفاصيل', 'العملاء مبيعات تحليلي',
                'تحليل فواتير العملاء', 'تفاصيل فواتير العملاء', 'تحليلي فواتير العملاء',
                'العملاء فواتير تحليل', 'العملاء فواتير تفاصيل', 'العملاء فواتير تحليلي',
                'تحليل مبيعات الزبائن', 'تفاصيل مبيعات الزبائن', 'تحليلي مبيعات الزبائن',
                'الزبائن مبيعات تحليل', 'الزبائن مبيعات تفاصيل', 'الزبائن مبيعات تحليلي',
                'تحليل فواتير الزبائن', 'تفاصيل فواتير الزبائن', 'تحليلي فواتير الزبائن',
                'الزبائن فواتير تحليل', 'الزبائن فواتير تفاصيل', 'الزبائن فواتير تحليلي',
                'تحليل مبيعات المشترين', 'تفاصيل مبيعات المشترين', 'تحليلي مبيعات المشترين',
                'المشترين مبيعات تحليل', 'المشترين مبيعات تفاصيل', 'المشترين مبيعات تحليلي',
                'تحليل فواتير المشترين', 'تفاصيل فواتير المشترين', 'تحليلي فواتير المشترين',
                'المشترين فواتير تحليل', 'المشترين فواتير تفاصيل', 'المشترين فواتير تحليلي',
                'تحليل مبيعات المستهلكين', 'تفاصيل مبيعات المستهلكين', 'تحليلي مبيعات المستهلكين',
                'المستهلكين مبيعات تحليل', 'المستهلكين مبيعات تفاصيل', 'المستهلكين مبيعات تحليلي',
                'تحليل فواتير المستهلكين', 'تفاصيل فواتير المستهلكين', 'تحليلي فواتير المستهلكين',
                'المستهلكين فواتير تحليل', 'المستهلكين فواتير تفاصيل', 'المستهلكين فواتير تحليلي',
                'تحليل مبيعات عميل', 'تحليلي مبيعات عميل', 'عميل مبيعات تحليلي',
                'تحليل فواتير عميل', 'تحليلي فواتير عميل', 'عميل فواتير تحليلي',
                'تحليل مبيعت مشتري', 'تحليلي مبيعات مشتري', 'مشتري مبيعات تحليلي',
                'تحليل فواتير مشتري', 'تحليلي فواتير مشتري', 'مشتري فواتير تحليلي',
                'تحليل مبيعات زبون', 'تحليلي مبيعات زبون', 'زبون مبيعات تحليلي',
                'تحليل فواتير زبون', 'تحليلي فواتير زبون', 'زبون فواتير تحليلي',
                'مبيعا في المبيعات التحليلية', 'مبيعا باستخدام المبيعات التحليلية'
                ],
                'negative': ['مردود', 'مرتجع', 'استرجاع'],
                'context': 'فواتير المبيعات الرئيسية',
                'description': 'يحتفظ ببيانات مفصلة عن العناصر الفردية ضمن كل معاملة بيع، مع تحديد تفاصيل العناصر لكل عملية بيع.',
            },
            'SALES_RT_BILL_MST_AI_VW': {
                'keywords': ['مردود', 'مرتجع', 'استرجاع', 'مردودات', 'مرتجعات',
                'مردود المبيعات', 'فاتورة مردود', 'فواتير مردود',
                'مردود رئيسي', 'مردودات رئيسية', 'رأس المردود', 'رؤوس المردود',
                'مردود مبيعات رئيسي', 'مردود مبيعات اجمالي', 'فواتير مردود رئيسية', 'فواتير مردود اجمالية',
                'اجمالي المردود', 'اجماليات المردود', 'رئيسي المردود', 'رئيسيات المردود',
                'مجاميع المردود', 'مجموع المردود', 'ملخص المردود', 'ملخصات المردود',
                'رأس فاتورة المردود', 'رؤوس فواتير المردود', 'معلومات رئيسية للمردود',
                'بيانات رئيسية لمردود المبيعات', 'معلومات اساسية للمردود', 'بيانات اساسية لمردود المبيعات',
                'ملخص فواتير المردود', 'اجماليات فواتير المردود', 'مجاميع فواتير المردود',
                'مرتجع', 'مرتجعات', 'مرتجع المبيعات', 'مرتجعات المبيعات', 'فاتورة مرتجع', 'فواتير مرتجعات',
                'مردود عميل', 'مردود العميل', 'مردودات العميل', 'مردودات العملاء',
                'مردود عملاء', 'مردود العملاء', 'مرتجع العميل', 'مرتجع العميل',
                'مرتجعات عميل', 'مرتجعات العميل', 'مرتجعات عملاء', 'مرتجعات العملاء',
                'فاتورة مردود', 'فاتورة مرتجع',
                ],
                'negative': ['تحليل', 'تحللي', 'تفاصيل'],
                'context': 'مردودات المبيعات الرئيسية',
                'description': 'يخزن البيانات المتعلقة بإرجاعات المبيعات، ويلتقط معلومات حول كل معاملة إرجاع على مستوى عالٍ.',
                'weight_multiplier': 2 ,
            },
            'SALES_RT_BILL_ANALYSIS_AI_VW': {
                'keywords': ['تحليل المردود', 'تحليلي المردود', 'مردود تحليلي',
                 'تحليل مردود المبيعات', 'مردود المبيعات تحليل',                 
                'تحليل المردود', 'المردود تحليل', 'تحيلي المردود', 'المردود تحليلي',
                'تحليل فواتير المردود', 'المردود فواتير تحليل', 'تحليلي فواتير المردود', 'المردود فواتير تحليلي',
                'تفاصيل المردود', 'المردود تفاصيل', 'تفاصيل مردود امبيعات', 'مردود المبيعات تفاصيل',
                'تفصيلي المردود', 'المردود تفصيلي', 'تفصيلي مردود المبيعات', 'مردود المبيعات تفصيلي',
                'احصائيات المردود', 'المردود احصائيات', 'احصائيات مردود المبيعات', 'مردود المبيعات احصائيات',
                'تقارير المردود', 'المردود تقارير', 'تقارير مردود المبيعات', 'مردود المبيعات تقارير',
                'تحليلة المردود', 'المردود تحليلة', 'تحليلية المردود', 'المردود تحليلية', 'المردود التحليلية',
                'تحليلة فواتير المردود', 'المردود فواتير تحليلة', 'تحليلية فواتير المردود', 'المردود فواتير تحليلية',
                'تفاصيل كاملة للمردود', 'تفاصيل كاملة لمردود المبيعات', 'تحليل كامل للمردود', 'تحليل كامل لمردود المبيعات',
                'تحليل شامل للمردود', 'تحليل شامل لمردود المبيعات', 'تفاصيل شاملة للمردود', 'تفاصيل شاملة لمردود المبيعات',
                'تحليل مفصل للمردود', 'تحليل مفصل لمردود المبيعات', 'تفاصيل مفصلة للمردود', 'تفاصيل مفصلة لمردود المبيعات',
                'مرتجع المبيعات', 'مرتجعات المبيعات', 'تحليل المرتجعات', 'تفاصيل المرتجعات',
                'تحليل مردود عميل', 'تحليلي مردود عميل', 'مردود عميل تحليلي', 'تفاصيل مردود عميل',
                'تحليل مردود العميل', 'تحليلي مردود لعميل', 'مدود العميل تحليلي', 'تفاصيل مردود العميل',
                'تحليلي مردود عملاء', 'مردود عملاء تحليلي', 'تحليل مردود عملاء', 'تفاصيل مردود عملاء',
                'مجموع مردود المبيعات التحللي', 'مجموع المردود التحليلي',
                'ما هو مجموع التحليلي للمردود المبيعات', 'مجموع التحليلي للمردود المبيعات'
                ],
                'context': 'تحليل مردودات المبيعات',
                'description': 'يحتوي على بيانات مفصلة عن العناصر الفردية المشاركة في كل معاملة إرجاع مبيعات، مع تفصيل معلومات الإرجاع الخاصة بالعنصر.'
            },
            'PURCHS_BILL_MST_AI_VW': {
                'keywords': ['فواتير المشتريات', 'مشتريات', 'فاتورة مشتريات', 'فواتير شراء', 'فاتورة شراء','مشتريا', 'مشترياً',
                'مشتريات', 
                'مشتريات', 'فاتورة مشتريات', 'فواتير مشتريات',
                'مشتريات رئيسية', 'مشتريات اجمالية', 'فواتير مشتريات رئيسية', 'فواتير مشتريات اجمالية',
                'اجمالي المشتريات', 'اجماليات المشتريات', 'رئيسي المشتريات', 'رئيسيات المشتريات',
                'مجاميع المشتريات', 'مجموع المشتريات', 'ملخص المشتريات', 'ملخصات المشتريات',
                'رأس فاتورة المشتريات', 'رؤوس فواتير المشتريات', 'معلومات رئيسية للمشتريات', 'معلومات اساسية للمشتريات',
                'ملخص فواتير المشتريات', 'اجماليات فواتير المشتريات', 'مجاميع فواتير المشتريات',
                'مشتريات المورد', 'مشتريات الموردين','مورد','موردين',
                'فواتي المورد', 'فواتير الموردين',
                'مشتريات من المورد', 'مشتريات من الموردين',
                'فواتير من المورد', 'فواتير من الموردين'],
                'negative': ['مردود', 'مرتجع', 'استرجاع', 'تحليل', 'تحليلي'],
                'context': 'فواتير المشتريات الرئيسية',
                'description': 'يحتفظ ببيانات عالية المستوى حول معاملات الشراء، بما في ذلك تفاصيل الشراء على مستوى الفاتورة أو المعاملة.'
            },
            'PURCHS_BILL_ANALYSIS_AI_VW': {
                'keywords': ['تحليل المشتريات', 'تحليلي المشتريات', 'تفاصيل المشتريات', 'المشتريات تحليل',
                           'تحليل فواتير المشتريات', 'تفاصيل فواتير المشتريات','تحليل المشتريات', 'المشتريات تحليل',                 
                'تحليل المشتريات', 'المشتريات تحليل', 'تحليلي المشتريات', 'المشتريات تحليلي',
                'تحليل فواتير المشتريات', 'المشتريات فواتير تحليل', 'تحليلي فواتير المشتريات', 'المشتريات فواتير تحليلي',
                'تفاصيل المشتريات', 'المشتريات تفاصيل',
                'تفصيلي المشتريات', 'المشتريات تفصيلي', 
                'احصائيات المشتريات', 'المشتريات احصائيات', 
                'تقارير المشتريات', 'المشتريات تقارير',
                'تحليلة المشتريات', 'المشتريات تحليلة', 'تحليلية المشتريات', 'المشريات تحليلية', 'المشتريات التحليلية',
                'تحليلة فواتير المشتريات', 'المشتريات فواتير تحليلة', 'تحليلية فواتير المشتريات', 'المشتريات فواتير تحليلة',
                'تفاصيل كاملة للمشتريات', 'تحليل كامل للمشتريات',
                'تحليل شامل للمشتريات', 'تفاصيل شاملة للمشتريات',
                'تحليل مفصل للمشتريات', 'تفاصيل مفصلة للمشتريات',
                'تحليل مشتريات الموردين', 'تفاصيل مشتريات الموردين', 'تحليلي متريات الموردين',
                'الموردين مشتريات تحليل', 'الموردين مشتريات تفاصيل', 'الموردين مشتريات تحليلي',
                'تليل فواتير الموردين', 'تفاصيل فواتير الموردين', 'تحليلي فواتير الموردين',
                'الموردين فواتير تحليل', 'الموردين فواتير تفاصيل', 'الموردين فواتير تحليلي',
                'تحليل مشتريات موارد', 'تحليلي مشتريات موارد', 'مشتريات موارد تحليلي',
                'تحليل مشتريات الموارد', 'تحليلي مشتريات الموارد', 'مشتريات الموارد تحليلي'],
                'negative': ['مردود', 'مرتجع', 'استرجاع'],
                'context': 'تحليل فواتير المشتريات',
                'description': 'يحتوي على معلومات مفصلة حول العناصر داخل كل معاملة شراء، وتقسيم كل فاتورة إلى بيانات عنصر فردية.'
            },
            'GLS_PST_AI_VW': {
                'keywords': ['قيود', 'قيد', 'قيود محاسبية', 'قيد محاسبي', 'قيود اليومية', 'قيد يومية',
                 'قيود المحاسبة', 'قيد المحاسبة', 'قيود محاسبة', 'قيد محاسبة',
                'يومي عامة', 'قيود يومية', 'قيود يومية عامة', 'قيود يومية محاسبية',
                'يومية عامة', 'قيود يومية', 'سند قيد', 'سندات القيد', 'دفتر اليومية',
                'حركات الحسابات', 'حركة الحساب', 'القيود المحاسبية', 'القيود اليومية', 'القيود اليومية العامة',
                'سند محاسبي', 'سندات محاسبية', 'قيود محاسبية',
                'يومية الحسابات', 'دفتر الأستاذ', 'سجل القيود', 'حركات محاسبية',
                'سندات اليومية', 'حركة يومية', 'مستند قيد', 'قيود اليومية العامة',
                'سند يومية', 'قيود عامة', 'يومية مساعدة', 'قيود نظامية',
                'اليومية العامة للحسابات', 'دفتر اليومية العامة', 'سجل اليومية العامة',
                'يومية عامة للحسابات', 'دفتر القيد العامة', 'سجل القيود العامة',
                'يومية الحسابات العامة', 'دفتر الحسابات العامة', 'سجل الحسابات العامة',
                'يومية المحاسبة العامة', 'دفتر المحاسبة العامة', 'سجل المحاسبة العامة',
                'حسابات', 'حساب', 'الحسابات', 'الحساب', 'حسابات القيود', 'حسابات القيود اليومية',
                'قيود الحسابات', 'قيود الحسابات اليومية', 'حسابات يومية', 'حسابات اليومية',
                'قيود اليومية المحاسبية', 'قيود اليومية العامة المحاسبية', 'قيود يومية عامة محاسبية'],
                'weight_multiplier': 2,
                'negative': ['غير مرحل', 'غير مرحلة', 'تحت الترحيل'],
                'context': 'القيود المحاسبية',
                'description': 'يخزن البيانات المتعلقة بأرصدة مالية مختلفة، بما في ذلك أرصدة الحسابات وأرصدة النقد وأرصدة العملاء وأرصدة البنوك.'
            }
        }

        # إضافة السياقات باللغة الإنجليزية
        self.table_contexts_en = {
            'SALES_BILL_MST_AI_VW': {
                'keywords': [ 'Sales', 'Invoice', 'Invoices', 'Sale', 'Sold item', 'Sold item', 'Sales invoices', 'Sales', 'Sales', 'Invoice', 'Invoices', 'Sales', 'Invoice', 'Invoices', 'Main invoice', 'Main invoices', 'Invoice header', 'Invoice headers', 'Main sales', 'Total sales', 'Main sales invoices', 'Total sales invoices', 'Total sales', 'Sales totals', 'Main sales', 'Main sales', 'Sales aggregates', 'Total sales', 'Sales summary', 'Sales summaries', 'Sales invoice header', 'Sales invoice headers', 'Main information for sales', 'Main data for invoices', 'Basic information for sales', 'Basic data for invoices', 'Sales invoice summary', 'Sales invoice totals', 'Sales invoice aggregates', 'Customer invoices', 'Customer sales', 'Customer invoices', 'Customer sales', 'Buyer invoices', 'Buyer sales', 'Consumer invoices', 'Consumer sales', 'Customer', 'Customers', 'Customer sales', 'Customers sales', 'Customer invoice', 'Customer invoices', 'Customer invoices', 'Customer invoices', 'Sales of the customer', 'Sales of the customers', 'Customer invoices', 'Customer invoices'
               ],
                'negative': ['Returned item', 'Return', 'Analysis', 'Analytical','Returned', 'Retrieval'],
                'context': 'Main Sales Invoices',
                'description': 'Contains data on sales transactions, including high-level information about each sale at the bill or transaction level.'
            },
            'SALES_BILL_ANALYSIS_AI_VW': {
                'keywords': ['Sales Analysis', 'Analytical Sales', 'Sales Details', 'Sales Analysis', 'Sales Analysis', 'Sales Analysis', 'Analytical Sales', 'Sales Analytical', 'Sales Invoice Analysis', 'Sales Invoices Analysis', 'Analytical Sales Invoices', 'Sales Invoices Analytical', 'Sales Details', 'Sales Details', 'Invoice Details', 'Invoice Details', 'Sales Detailed', 'Sales Detailed', 'Invoice Detailed', 'Invoice Detailed', 'Sales Statistics', 'Sales Statistics', 'Invoice Statistics', 'Invoice Statistics', 'Sales Reports', 'Sales Reports', 'Invoice Reports', 'Invoice Reports', 'Sales Analytical', 'Sales Analytical', 'Sales Analytical', 'Sales Analytical', 'Analytical Sales', 'Sales Invoices Analytical', 'Sales Invoices Analytical', 'Analytical Sales Invoices', 'Sales Invoices Analytical', 'Complete Sales Details', 'Complete Invoice Details', 'Complete Sales Analysis', 'Complete Invoice Analysis', 'Comprehensive Sales Analysis', 'Comprehensive Invoice Analysis', 'Comprehensive Sales Details', 'Comprehensive Invoice Details', 'Detailed Sales Analysis', 'Detailed Invoice Analysis', 'Detailed Sales Details', 'Detailed Invoice Details', 'Sales Analysis for Customers', 'Sales Details for Customers', 'Analytical Sales for Customers', 'Customers Sales Analysis', 'Customers Sales Details', 'Customers Sales Analytical', 'Sales Invoice Analysis for Customers', 'Invoice Details for Customers', 'Analytical Invoices for Customers', 'Customers Invoices Analysis', 'Customers Invoices Details', 'Customers Invoices Analytical', 'Sales Analysis for Clients', 'Sales Details for Clients', 'Analytical Sales for Clients', 'Clients Sales Analysis', 'Clients Sales Details', 'Clients Sales Analytical', 'Sales Invoice Analysis for Clients', 'Invoice Details for Clients', 'Analytical Invoices for Clients', 'Clients Invoices Analysis', 'Clients Invoices Details', 'Clients Invoices Analytical', 'Sales Analysis for Buyers', 'Sales Details for Buyers', 'Analytical Sales for Buyers', 'Buyers Sales Analysis', 'Buyers Sales Details', 'Buyers Sales Analytical', 'Sales Invoice Analysis for Buyers', 'Invoice Details for Buyers', 'Analytical Invoices for Buyers', 'Buyers Invoices Analysis', 'Buyers Invoices Details', 'Buyers Invoices Analytical', 'Sales Analysis for Consumers', 'Sales Details for Consumers', 'Analytical Sales for Consumers', 'Consumers Sales Analysis', 'Consumers Sales Details', 'Consumers Sales Analytical', 'Sales Invoice Analysis for Consumers', 'Invoice Details for Consumers', 'Analytical Invoices for Consumers', 'Consumers Invoices Analysis', 'Consumers Invoices Details', 'Consumers Invoices Analytical', 'Sales Analysis for Customer', 'Analytical Sales for Customer', 'Customer Sales Analytical', 'Sales Invoice Analysis for Customer', 'Analytical Invoices for Customer', 'Customer Invoices Analytical', 'Sales Analysis for Buyer', 'Analytical Sales for Buyer', 'Buyer Sales Analytical', 'Sales Invoice Analysis for Buyer', 'Analytical Invoices for Buyer', 'Buyer Invoices Analytical', 'Sales Analysis for Client', 'Analytical Sales for Client', 'Client Sales Analytical', 'Sales Invoice Analysis for Client', 'Analytical Invoices for Client', 'Client Invoices Analytical'
                             'sales in analytical sales', 'sales using analytical sales'],
                'negative': ['Returned item', 'Return','Returned', 'Retrieval'],
                'context': 'Sales Invoice Analysis',
                'description': 'Holds detailed data on individual items within each sales transaction, specifying the breakdown of items per sale.'
            },
            'SALES_RT_BILL_MST_AI_VW': {
                'keywords': ['Return', 'Returned item', 'Returns', 'Sales Return', 'Return Invoice', 'Return Invoices', 'Main Return', 'Main Returns', 'Return Header', 'Return Headers', 'Main Sales Return', 'Total Sales Return', 'Main Return Invoices', 'Total Return Invoices', 'Total Return', 'Return Totals', 'Main Return', 'Main Returns', 'Return Aggregates', 'Total Return', 'Return Summary', 'Return Summaries', 'Return Invoice Header', 'Return Invoice Headers', 'Main Information for Returns', 'Main Data for Sales Returns', 'Basic Information for Returns', 'Basic Data for Sales Returns', 'Return Invoice Summary', 'Return Invoice Totals', 'Return Invoice Aggregates', 'Return', 'Returns', 'Sales Return', 'Sales Returns', 'Return Invoice', 'Return Invoices', 'Customer Return', 'Customers Return', 'Customers Returns', 'Customers Returns', 'Customer Returns', 'Customers Returns', 'Customer Return', 'Customers Return', 'Customer Returns', 'Customers Returns', 'Customer Returns', 'Return Invoice', 'Return Invoice'
                ],
                'negative': ['Analysis', 'Analytical', 'Details'],
                'context': 'Main Sales Returns',
                'description': 'Stores data related to sales returns, capturing information about each return transaction at a high level.'
            },
            'SALES_RT_BILL_ANALYSIS_AI_VW': {
                'keywords': ['Return Analysis', 'Analytical Return', 'Return Analytical', 'Sales Return Analysis', 'Sales Return Analysis', 'Return Analysis', 'Return Analysis', 'Analytical Return', 'Return Analytical', 'Return Invoice Analysis', 'Return Invoices Analysis', 'Analytical Return Invoices', 'Return Invoices Analytical', 'Return Details', 'Return Details', 'Sales Return Details', 'Sales Return Details', 'Detailed Return', 'Return Detailed', 'Detailed Sales Return', 'Sales Return Detailed', 'Return Statistics', 'Return Statistics', 'Sales Return Statistics', 'Sales Return Statistics', 'Return Reports', 'Return Reports', 'Sales Return Reports', 'Sales Return Reports', 'Return Analysis', 'Return Analysis', 'Analytical Return', 'Return Analytical', 'The Analytical Return', 'Return Invoices Analysis', 'Return Invoices Analysis', 'Analytical Return Invoices', 'Return Invoices Analytical', 'Complete Details for Return', 'Complete Details for Sales Return', 'Complete Analysis for Return', 'Complete Analysis for Sales Return', 'Comprehensive Analysis for Return', 'Comprehensive Analysis for Sales Return', 'Comprehensive Details for Return', 'Comprehensive Details for Sales Return', 'Detailed Analysis for Return', 'Detailed Analysis for Sales Return', 'Detailed Details for Return', 'Detailed Details for Sales Return', 'Sales Return', 'Sales Returns', 'Returns Analysis', 'Returns Details', 'Customer Return Analysis', 'Analytical Customer Return', 'Customer Return Analytical', 'Customer Return Details', 'Customer Return Analysis', 'Analytical Customer Return', 'Customers Return Analytical', 'Customers Return Details', 'Analytical Customer Returns', 'Customer Returns Analytical', 'Customers Return Analysis', 'Customers Return Details', 'Analytical Sales Return Total', 'Analytical Return Total', 'What is the analytical total of sales returns', 'Analytical total of sales returns'
                            ],
                'context': 'Sales Returns Analysis',
                'description': 'Contains detailed data on individual items involved in each sales return transaction, detailing item-specific return information.'
            },
            'PURCHS_BILL_MST_AI_VW': {
                'keywords': ['Purchase Invoices', 'Purchases', 'Purchase Invoice', 'Purchase Invoices', 'Purchase Invoice', 'Purchaser', 'Purchaser', 'Purchases', 'Purchases', 'Purchase Invoice', 'Purchase Invoices', 'Main Purchases', 'Total Purchases', 'Main Purchase Invoices', 'Total Purchase Invoices', 'Total Purchases', 'Purchases Totals', 'Main Purchases', 'Main Purchases', 'Purchases Aggregates', 'Total Purchases', 'Purchase Summary', 'Purchase Summaries', 'Purchase Invoice Header', 'Purchase Invoice Headers', 'Main Information for Purchases', 'Basic Information for Purchases', 'Purchase Invoice Summary', 'Purchase Invoice Totals', 'Purchase Invoice Aggregates', 'Supplier Purchases', 'Suppliers Purchases', 'Supplier', 'Suppliers', 'Supplier Invoices', 'Suppliers Invoices', 'Purchases from Supplier', 'Purchases from Suppliers', 'Invoices from Supplier', 'Invoices from Suppliers'
                            ],
                'negative': ['Return', 'Returned item', 'Retrieval', 'Analysis', 'Analytical','Returned'],
                'context': 'Main Purchase Invoices',
                'description': 'Holds high-level data on purchase transactions, including purchase details at the bill or transaction level.'
            },
            'PURCHS_BILL_ANALYSIS_AI_VW': {
                'keywords': ['Purchases Analysis', 'Analytical Purchases', 'Purchases Details', 'Purchases Analysis', 'Purchases Invoices Analysis', 'Purchases Invoices Details', 'Purchases Analysis', 'Purchases Analysis', 'Purchases Analysis', 'Purchases Analysis', 'Analytical Purchases', 'Purchases Analytical', 'Purchases Invoices Analysis', 'Purchases Invoices Analysis', 'Analytical Purchases Invoices', 'Purchases Invoices Analytical', 'Purchases Details', 'Purchases Details', 'Detailed Purchases', 'Purchases Detailed', 'Purchases Statistics', 'Purchases Statistics', 'Purchases Reports', 'Purchases Reports', 'Purchases Analytical', 'Purchases Analytical', 'Purchases Analytical', 'Purchases Analytical', 'The Analytical Purchases', 'Purchases Invoices Analytical', 'Purchases Invoices Analytical', 'Purchases Invoices Analytical', 'Purchases Invoices Analytical', 'Complete Details for Purchases', 'Complete Analysis for Purchases', 'Comprehensive Analysis for Purchases', 'Comprehensive Details for Purchases', 'Detailed Analysis for Purchases', 'Detailed Details for Purchases', 'Suppliers Purchases Analysis', 'Suppliers Purchases Details', 'Analytical Suppliers Purchases', 'Suppliers Purchases Analysis', 'Suppliers Purchases Details', 'Suppliers Purchases Analytical', 'Suppliers Invoices Analysis', 'Suppliers Invoices Details', 'Analytical Suppliers Invoices', 'Suppliers Invoices Analysis', 'Suppliers Invoices Details', 'Suppliers Invoices Analytical', 'Resources Purchases Analysis', 'Analytical Resources Purchases', 'Resources Purchases Analytical', 'Resources Purchases Analysis', 'Analytical Resources Purchases', 'Resources Purchases Analytical'],
                'negative': ['Return', 'Returned item', 'Retrieval','Returned'],
                'context': 'Purchase Invoice Analysis',
                'description': 'Contains detailed information on items within each purchase transaction, breaking down each bill into individual item data.'
            },
            'GLS_PST_AI_VW': {
                'keywords': ['Entries', 'Entry', 'Accounting Entries', 'Accounting Entry', 'Journal Entries', 'Journal Entry', 'Accounting Entries', 'Accounting Entry', 'Accounting Entries', 'Accounting Entry', 'General Journal', 'Journal Entries', 'General Journal Entries', 'Accounting Journal Entries', 'General Journal', 'Journal Entries', 'Journal Voucher', 'Journal Vouchers', 'Journal Book', 'Account Movements', 'Account Movement', 'Accounting Entries', 'Journal Entries', 'General Journal Entries', 'Accounting Voucher', 'Accounting Vouchers', 'Accounting Entries', 'Accounts Journal', 'General Ledger', 'Entries Register', 'Accounting Transactions', 'Daily Vouchers', 'Daily Movement', 'Entry Document', 'General Journal Entries', 'Daily Voucher', 'General Entries', 'Subsidiary Journal', 'Statutory Entries', 'General Journal of Accounts', 'General Journal Book', 'General Journal Register', 'General Journal for Accounts', 'General Entry Book', 'General Entries Register', 'General Accounts Journal', 'General Accounts Book', 'General Accounts Register', 'General Accounting Journal', 'General Accounting Book', 'General Accounting Register', 'Accounts', 'Account', 'Accounts', 'Account', 'Entry Accounts', 'Journal Entry Accounts', 'Account Entries', 'Daily Account Entries', 'Daily Accounts', 'Journal Accounts', 'Accounting Journal Entries', 'General Accounting Journal Entries', 'General Accounting Journal Entries'
                             ],
                'weight_multiplier': 2,
                'negative': ['Unposted', 'Unposted', 'Under Posting'],
                'context': 'Accounting Entries',
                'description': 'Stores data related to various financial balances, including account balances, cash balances, customer balances, and bank balances.'
            }
        }

    def get_table_context(self, natural_query):
        """تحديد الجدول المناسب بناءً على محتوى السؤال مع مراعاة السياق"""
        try:
            # تحديد لغة السؤال
            is_english = self._is_english_query(natural_query)
            
            query = self._normalize_query(natural_query)
            best_match = None
            max_score = -1

            # اختيار السياقات المناسبة بناءً على اللغة
            contexts = self.table_contexts_en if is_english else self.table_contexts

            # تحليل السياق أولاً
            if is_english:
                has_return = any(word in query.lower() for word in ['return', 'returns', 'returned'])
                has_sales = any(word in query.lower() for word in ['sales', 'sale', 'selling', 'sold'])
                has_analysis = any(word in query.lower() for word in ['analysis', 'analytical', 'details', 'statistics', 'comprehensive'])
                
                # التحقق من كلمات الأرصدة باللغة الإنجليزية
                balance_keywords = ['balance', 'balances', 'account balance', 'account balances',
                                  'cash balance', 'cash balances', 'customer balance', 'customer balances',
                                  'bank balance', 'bank balances', 'financial balance', 'financial balances']
                has_balance = any(keyword.lower() in query.lower() for keyword in balance_keywords)
                
                if has_balance:
                    return 'GLS_PST_AI_VW', self.database_schemas.get('GLS_PST_AI_VW'), contexts
                    
                # إذا كان السؤال يتعلق بمردود المبيعات
                if has_return and has_sales:
                    if has_analysis:
                        relevant_tables = {k: v for k, v in contexts.items() 
                                         if k == 'SALES_RT_BILL_ANALYSIS_AI_VW'}
                    else:
                        relevant_tables = {k: v for k, v in contexts.items() 
                                         if k == 'SALES_RT_BILL_MST_AI_VW'}
                elif has_sales and not has_return:
                    if has_analysis:
                        relevant_tables = {k: v for k, v in contexts.items()
                                         if k == 'SALES_BILL_ANALYSIS_AI_VW'}
                    else:
                        relevant_tables = {k: v for k, v in contexts.items()
                                         if k == 'SALES_BILL_MST_AI_VW'}
                else:
                    relevant_tables = contexts
            else:
                has_mardood = any(word in query for word in ['مردود', 'مرتجع', 'مردودات', 'مرتجعات'])
                has_sales = 'مبيعات' in query or 'بيع' in query
                has_analysis = any(word in query for word in ['تحليلي', 'تحليل', 'تفصيلي', 'تفاصيل', 'احصائيات', 'شامل', 'التحليلية', 'تحليلية'])
                
                # التحقق من كلمات الأرصدة باللغة العربية
                balance_keywords = ['رصيد', 'ارصدة', 'أرصدة', 'رصيد حساب', 'ارصدة حسابات', 
                                  'رصيد نقدي', 'ارصدة نقدية', 'رصيد عميل', 'ارصدة عملاء',
                                  'رصيد بنك', 'ارصدة بنوك', 'رصيد مالي', 'ارصدة مالية']
                has_balance = any(keyword in query for keyword in balance_keywords)
                
                if has_balance:
                    return 'GLS_PST_AI_VW', self.database_schemas.get('GLS_PST_AI_VW'), contexts
                    
                if has_mardood and has_sales:
                    if has_analysis:
                        relevant_tables = {k: v for k, v in contexts.items() 
                                         if k == 'SALES_RT_BILL_ANALYSIS_AI_VW'}
                    else:
                        relevant_tables = {k: v for k, v in contexts.items() 
                                         if k == 'SALES_RT_BILL_MST_AI_VW'}
                elif has_sales and not has_mardood:
                    if has_analysis:
                        relevant_tables = {k: v for k, v in contexts.items()
                                         if k == 'SALES_BILL_ANALYSIS_AI_VW'}
                    else:
                        relevant_tables = {k: v for k, v in contexts.items()
                                         if k == 'SALES_BILL_MST_AI_VW'}
                else:
                    relevant_tables = contexts

            # بعد تحديد الجداول المناسبة، نحسب درجة التطابق لكل جدول
            for table_name, context in relevant_tables.items():
                if table_name != 'GLS_PST_AI_VW':  # نتجاهل GLS_PST_AI_VW لأننا عالجناه بالفعل
                    context_score = self._calculate_context_score(query, context)
                    weight_multiplier = context.get('weight_multiplier', 1)
                    final_score = context_score * weight_multiplier

                    # زيادة الدرجة إذا كان السياق يتطابق بشكل كامل
                    if (is_english and has_return and 'SALES_RT' in table_name) or \
                       (not is_english and has_mardood and 'SALES_RT' in table_name):
                        final_score *= 2
                    
                    if final_score > max_score:
                        max_score = final_score
                        best_match = table_name

            if best_match and max_score > 0:
                return best_match, self.database_schemas.get(best_match), contexts
            return None, None, contexts

        except Exception as e:
            print(f"Error in get_table_context: {str(e)}")
            return None, None, contexts

    def _normalize_query(self, query):
        """تنظيف وتوحيد صيغة السؤال"""
        # تحديد نوع اللغة
        is_english = self._is_english_query(query)
        
        if is_english:
            return query.lower().strip()
        else:
            return query.replace('أ', 'ا').replace('إ', 'ا').replace('ة', 'ه').lower()

    def _calculate_context_score(self, query, context):
        """حساب درجة التطابق مع سياق الجدول"""
        score = 0
        words = query.split()
        
        # التحقق من الكلمات المفتاحية الإيجابية
        for keyword in context['keywords']:
            if self._is_english_query(query):
                if keyword.lower() in query.lower():
                    weight = len(keyword.split()) * 2
                    score += weight
            else:
                if keyword in query:
                    weight = len(keyword.split()) * 2
                    score += weight

        # خصم النقاط للكلمات السلبية
        for negative in context.get('negative', []):
            if self._is_english_query(query):
                if negative.lower() in query.lower():
                    score -= 5
            else:
                if negative in query:
                    score -= 5

        # إضافة نقاط للسياق العام
        if self._is_english_query(query):
            if context['context'].lower() in query.lower():
                score += 3
        else:
            if context['context'] in query:
                score += 3

        # التحقق من تسلسل الكلمات
        for i in range(len(words) - 1):
            phrase = f"{words[i]} {words[i+1]}"
            if self._is_english_query(query):
                if any(phrase.lower() in keyword.lower() for keyword in context['keywords']):
                    score += 2
            else:
                if any(phrase in keyword for keyword in context['keywords']):
                    score += 2

        return score


    def _is_english_query(self, query):
        """التحقق مما إذا كان السؤال باللغة الإنجليزية"""
        english_chars = sum(1 for c in query if ord('a') <= ord(c.lower()) <= ord('z'))
        arabic_chars = sum(1 for c in query if '\u0600' <= c <= '\u06FF')
        return english_chars > arabic_chars
