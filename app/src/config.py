# معلومات قاعدة البيانات

CONFIG_DB = "ys_taiz/ys123@localhost:1521/orcl"


# مسار مجلد ملفات Excel
EXCEL_FOLDER_PATH = 'AI_VIEW_COMMENT'

OWNER="IAS20241"


# ترجمة أسماء الجداول بالعربي
TABLES_AR = {
    'GLS_PST_AI_VW': 'اليومية العامة للحسابات',
    'SALES_BILL_MST_AI_VW': 'المبيعات رئيسية',
    'SALES_BILL_ANALYSIS_AI_VW': 'المبيعات تحليلية',
    'PURCHS_BILL_MST_AI_VW': 'المشتريات رئيسية',
    'PURCHS_BILL_ANALYSIS_AI_VW': 'المشتريات تحليلية',
    'SALES_RT_BILL_MST_AI_VW': 'مردود المبيعات رئيسية',
    'SALES_RT_BILL_ANALYSIS_AI_VW': 'مردود المبيعات تحليلية'
}

TABLES_EN = {
    'GLS_PST_AI_VW': 'General Journal of Accounts',
    'SALES_BILL_MST_AI_VW': 'Main Sales',
    'SALES_BILL_ANALYSIS_AI_VW': 'Sales Analytical',
    'PURCHS_BILL_MST_AI_VW': 'Main Purchases',
    'PURCHS_BILL_ANALYSIS_AI_VW': 'Purchases Analytical',
    'SALES_RT_BILL_MST_AI_VW': 'Main Sales Returns',
    'SALES_RT_BILL_ANALYSIS_AI_VW': 'Sales Returns Analytical'
}

# إعدادات أخرى يمكن إضافتها هنا
SCHEMA_FILE = 'database_schemas.json' 