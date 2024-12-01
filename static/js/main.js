let sidebarOpen = true;
const sidebar = document.querySelector('.sidebar');
const mainContent = document.querySelector('.main-content');
const collapseBtn = document.querySelector('.collapse-btn-group');
const restoreBtn = document.querySelector('.restore-sidebar');

// دالة لحفظ حالة السايدبار
function saveSidebarState(isVisible) {
    localStorage.setItem('sidebarVisible', isVisible);
}

// دالة إخفاء السايدبار
function collapseSidebar() {

    
    // إخفاء السايدبار
    sidebar.style.transform = 'translateX(100%)';
    sidebar.style.opacity = '0';
    
    // تمديد المحتوى الرئيسي
    mainContent.style.marginRight = '0';
    mainContent.style.width = '100%';
    
    // تبديل الأزرار
    collapseBtn.style.display = 'none';
    restoreBtn.style.display = 'flex';
    
    document.body.classList.add('sidebar-hidden');
    sidebarOpen = false;
    
    // حفظ الحالة
    saveSidebarState(false);
}

// دالة إظهار السايدبار
function restoreSidebar() {
    
    // إظهار السايدبار
    sidebar.style.transform = 'translateX(0)';
    sidebar.style.opacity = '1';
    
    // تقليص المحتوى الرئيسي
    mainContent.style.marginRight = '285px';
    mainContent.style.width = 'calc(100% - 250px)';
    
    // تبديل الأزرار
    collapseBtn.style.display = 'flex';
    restoreBtn.style.display = 'none';
    
    document.body.classList.remove('sidebar-hidden');
    sidebarOpen = true;
    
    // حفظ الحالة
    saveSidebarState(true);
}

// التحقق من الحالة المحفوظة
try {
    const sidebarVisible = localStorage.getItem('sidebarVisible');
    
    // إذا كانت القيمة المحفوظة false، قم بإخفاء السايدبار
    if (sidebarVisible === 'false') {
        collapseSidebar();
    } else {
        // في حالة عدم وجود قيمة محفوظة أو القيمة true، قم بإظهار السايدبار
        restoreSidebar();
    }
} catch (error) {
    console.error('Error loading sidebar state:', error);
    // في حالة حدوث خطأ، نفترض أن السايدبار يجب أن يكون مرئياً
    restoreSidebar();
}

// إضافة مستمعات الأحداث
if (collapseBtn) {
    collapseBtn.addEventListener('click', collapseSidebar);
}

if (restoreBtn) {
    restoreBtn.addEventListener('click', restoreSidebar);
}