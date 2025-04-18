from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

def register_arabic_fonts():
    fonts_dir = os.path.join(os.path.dirname(__file__), 'fonts')
    
    # تسجيل الخطوط العربية
    font_files = {
        'TraditionalArabic': 'trado.ttf',
        'NotoNaskhArabic': 'NotoNaskhArabic-Regular.ttf',
        'Amiri': 'Amiri-Regular.ttf',
        'Cairo': 'Cairo-Regular.ttf'
    }
    
    for font_name, font_file in font_files.items():
        font_path = os.path.join(fonts_dir, font_file)
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont(font_name, font_path))

def get_arabic_styles():
    # تسجيل الخطوط العربية
    register_arabic_fonts()
    styles = getSampleStyleSheet()
    
    # أنماط النصوص العربية
    # نمط العنوان الرئيسي
    styles.add(ParagraphStyle(
        name='ArabicTitle',
        fontName='Cairo',
        fontSize=24,
        leading=28,
        alignment=TA_CENTER,
        spaceAfter=30,
        textColor=colors.HexColor('#2C3E50'),
        borderPadding=10,
        borderColor=colors.HexColor('#BDC3C7'),
        borderWidth=1,
        backColor=colors.HexColor('#ECF0F1')
    ))
    
    # نمط النص العادي
    styles.add(ParagraphStyle(
        name='ArabicNormal',
        fontName='NotoNaskhArabic',
        fontSize=14,
        leading=22,
        alignment=TA_RIGHT,
        textColor=colors.HexColor('#2C3E50'),
        spaceBefore=6,
        spaceAfter=6,
        firstLineIndent=20
    ))
    
    # نمط النص الصغير
    styles.add(ParagraphStyle(
        name='ArabicSmall',
        fontName='Amiri',
        fontSize=12,
        leading=16,
        alignment=TA_RIGHT,
        textColor=colors.HexColor('#7F8C8D'),
        spaceBefore=4,
        spaceAfter=4
    ))
    
    # نمط عنوان الجدول
    styles.add(ParagraphStyle(
        name='ArabicTableHeader',
        fontName='Cairo',
        fontSize=14,
        leading=18,
        alignment=TA_CENTER,
        textColor=colors.white,
        backColor=colors.HexColor('#34495E')
    ))
    
    # نمط محتوى الجدول
    styles.add(ParagraphStyle(
        name='ArabicTableCell',
        fontName='NotoNaskhArabic',
        fontSize=12,
        leading=16,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#2C3E50')
    ))
    
    return {
        'Title': styles['ArabicTitle'],
        'Normal': styles['ArabicNormal'],
        'Small': styles['ArabicSmall'],
        'TableHeader': styles['ArabicTableHeader'],
        'TableCell': styles['ArabicTableCell']
    }