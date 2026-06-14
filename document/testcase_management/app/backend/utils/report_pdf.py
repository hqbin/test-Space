"""
测试报告PDF生成工具

与审核报告页面(ReportReview.vue)格式完全一致
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak, KeepTogether
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
import os
import platform
import logging
import traceback
from datetime import datetime
from xml.sax.saxutils import escape as xml_escape
from utils.report_conclusion import get_conclusion_and_criteria, get_selected_fields, filter_cover_rows, is_field_visible, get_zmind_conclusion

logger = logging.getLogger(__name__)


def _safe_text(text):
    """转义文本中的XML特殊字符，防止Paragraph解析出错导致乱码。
    保留已有的 <br/> 和 <b></b> 标签。"""
    if not text:
        return text
    s = str(text)
    # 先把合法标签替换为占位符
    s = s.replace('<br/>', '\x00BR\x00')
    s = s.replace('<b>', '\x00B\x00').replace('</b>', '\x00/B\x00')
    # 转义XML特殊字符
    s = xml_escape(s)
    # 恢复合法标签
    s = s.replace('\x00BR\x00', '<br/>')
    s = s.replace('\x00B\x00', '<b>').replace('\x00/B\x00', '</b>')
    return s


def _truncate_text(text, max_length=300):
    """截断过长的文本，超出部分用省略号代替。"""
    if not text:
        return text
    s = str(text)
    if len(s) > max_length:
        return s[:max_length] + "..."
    return s


def register_chinese_font():
    """注册中文字体。
    优先使用系统 TTF/TTC 字体（效果更好），
    找不到则回退到 reportlab 内置 CID 字体 STSong-Light（无需系统字体文件）。
    """
    # 1) 尝试系统 TTF/TTC 字体
    try:
        if platform.system() == 'Windows':
            font_candidates = [
                ('C:/Windows/Fonts/msyh.ttc', 0),
                ('C:/Windows/Fonts/simsun.ttc', 0),
                ('C:/Windows/Fonts/simhei.ttf', None),
            ]
        else:
            font_candidates = [
                ('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc', 0),
                ('/usr/share/fonts/truetype/wqy/wqy-microhei.ttc', 0),
                ('/usr/share/fonts/truetype/arphic/uming.ttc', 0),
                ('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', 0),
                ('/usr/share/fonts/google-noto-cjk/NotoSansCJK-Regular.ttc', 0),
                ('/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc', 0),
            ]
        
        for font_path, sub_index in font_candidates:
            if os.path.exists(font_path):
                if sub_index is not None:
                    pdfmetrics.registerFont(TTFont('ChineseFont', font_path, subfontIndex=sub_index))
                else:
                    pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                return 'ChineseFont'
    except Exception as e:
        print(f"TTF字体注册失败: {e}")

    # 2) 回退到 reportlab 内置 CID 字体（不需要系统字体文件）
    try:
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont
        pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
        return 'STSong-Light'
    except Exception as e:
        print(f"CID字体注册失败: {e}")

    return 'Helvetica'


def _calc_first_page_style_params(cover_row_count, result_row_count, has_zmind, include_pr_closed):
    """根据第一页内容量计算自适应样式参数。
    
    A4可用高度 ≈ 283mm (297 - 7*2 margins)
    预估各部分高度，选择 normal / compact 参数集。
    """
    # 固定部分高度(mm): logo(8) + title(12) + spacers
    fixed_h = 20
    
    # 封面表格：每行高度 = font行高 + padding*2 + border
    # normal: ~20mm/row, compact: ~13mm/row (双语label占2行)
    cover_row_h_normal = 20
    cover_row_h_compact = 13
    
    # result表格：header + data rows + total + passed + section title + note
    # normal: ~7mm/row, compact: ~5mm/row
    result_rows_total = result_row_count + 3  # header + data + Total + Passed
    result_row_h_normal = 7
    result_row_h_compact = 5
    result_extra_normal = 16  # section title + note + spacers
    result_extra_compact = 10
    
    # zmind表格：header + 1~3 data rows + note
    zmind_rows = 0
    if has_zmind:
        zmind_rows = (4 if include_pr_closed else 2)  # header + data rows
    zmind_row_h_normal = 7
    zmind_row_h_compact = 5
    zmind_extra_normal = 14  # spacers + severity note
    zmind_extra_compact = 8
    
    # 计算 normal 模式总高度
    h_normal = fixed_h
    h_normal += cover_row_count * cover_row_h_normal + 6  # spacer after cover
    h_normal += result_rows_total * result_row_h_normal + result_extra_normal
    if has_zmind:
        h_normal += zmind_rows * zmind_row_h_normal + zmind_extra_normal
    
    page_h = 283  # A4可用高度mm (297 - 7*2 margins)
    
    if h_normal <= page_h:
        # 内容少，用正常尺寸
        return {
            'label_font': 8, 'content_font': 8, 'cell_font': 7,
            'note_font': 7, 'section_font': 11, 'conclusion_font': 9,
            'okng_font': 7, 'copyright_font': 7,
            'label_leading': 11, 'content_leading': 11, 'cell_leading': 10,
            'cover_padding': 5, 'cell_padding': 3, 'section_padding': 5,
            'spacer_after_title': 3, 'spacer_after_cover': 6,
            'spacer_after_result': 1, 'spacer_after_note': 3,
            'spacer_after_zmind': 1,
        }
    else:
        # 内容多，用紧凑尺寸
        return {
            'label_font': 7, 'content_font': 7, 'cell_font': 6,
            'note_font': 6, 'section_font': 9, 'conclusion_font': 8,
            'okng_font': 6, 'copyright_font': 6,
            'label_leading': 9, 'content_leading': 9, 'cell_leading': 8,
            'cover_padding': 3, 'cell_padding': 2, 'section_padding': 3,
            'spacer_after_title': 1, 'spacer_after_cover': 3,
            'spacer_after_result': 1, 'spacer_after_note': 2,
            'spacer_after_zmind': 1,
        }


def generate_report_pdf(report_data, test_results, zmind_stats, test_cases, issue_list, output_path):
    """
    生成测试报告PDF，与审核报告页面格式完全一致
    """
    font_name = register_chinese_font()
    
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=7*mm,
        leftMargin=7*mm,
        topMargin=7*mm,
        bottomMargin=7*mm
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # ===== 预计算内容量，决定自适应样式参数 =====
    include_pr_closed = report_data.get('include_pr_closed', 0)
    has_zmind_csv = report_data.get('has_zmind_csv', False)
    project_name = report_data.get('project_name', '')
    
    template_config = report_data.get('report_template_config')
    selected_fields = get_selected_fields(template_config)
    
    _pre_cover_keys = [
        (None, '', ''),
        ('test_cycle', '', ''), ('testers', '', ''), ('reviewer_name', '', ''),
        (None, '', ''), (None, '', ''),
        ('test_conclusion', '', ''), ('release_criteria', '', ''),
        (None, '', ''), ('remark', '', ''),
    ]
    _pre_cover_rows = filter_cover_rows(_pre_cover_keys, selected_fields)
    cover_row_count = len(_pre_cover_rows)
    
    has_zmind_section = is_field_visible(selected_fields, 'zmind_stats') and has_zmind_csv and zmind_stats
    has_result_section = is_field_visible(selected_fields, 'test_results')
    result_module_count = len(test_results) if has_result_section else 0
    
    sp = _calc_first_page_style_params(cover_row_count, result_module_count, has_zmind_section, include_pr_closed)
    
    # ===== 样式定义（使用自适应参数） =====
    copyright_style = ParagraphStyle(
        'CopyrightStyle', parent=styles['Normal'],
        fontName=font_name, fontSize=sp['copyright_font'], textColor=colors.Color(0.4, 0.4, 0.4),
        alignment=TA_RIGHT
    )
    
    section_title_style = ParagraphStyle(
        'SectionTitleStyle', parent=styles['Normal'],
        fontName=font_name, fontSize=sp['section_font'], textColor=colors.black,
        alignment=TA_CENTER, leading=sp['section_font'] + 3
    )
    
    label_style = ParagraphStyle(
        'LabelStyle', parent=styles['Normal'],
        fontName=font_name, fontSize=sp['label_font'], textColor=colors.black,
        alignment=TA_CENTER, leading=sp['label_leading']
    )
    
    content_style = ParagraphStyle(
        'ContentStyle', parent=styles['Normal'],
        fontName=font_name, fontSize=sp['content_font'], textColor=colors.black,
        alignment=TA_LEFT, leading=sp['content_leading']
    )
    
    table_cell_style = ParagraphStyle(
        'TableCellStyle', parent=styles['Normal'],
        fontName=font_name, fontSize=sp['cell_font'], textColor=colors.black,
        alignment=TA_CENTER, leading=sp['cell_leading']
    )
    
    note_style = ParagraphStyle(
        'NoteStyle', parent=styles['Normal'],
        fontName=font_name, fontSize=sp['note_font'], textColor=colors.Color(0.4, 0.4, 0.4),
        alignment=TA_LEFT, leading=sp['cell_leading']
    )
    
    # 颜色定义 - 与审核页面一致
    orange_bg = colors.Color(1.0, 0.8, 0.6)       # #FFCC99
    gray_bg = colors.Color(0.906, 0.902, 0.902)    # #E7E6E6
    light_gray_bg = colors.Color(0.949, 0.949, 0.949)  # #F2F2F2
    black_border_color = colors.black
    
    # ==================== 版权信息（Logo + 文字） ====================
    logo_path = report_data.get('logo_path', '')
    copyright_text_content = f"Confidential &amp; Proprietary<br/>Copyright © {datetime.now().year} Whale TV Information Technology"
    
    if logo_path and os.path.exists(logo_path):
        try:
            logo_img = Image(logo_path, width=60, height=18)
            # 用表格实现左Logo右文字的布局
            header_data = [[logo_img, Paragraph(copyright_text_content, copyright_style)]]
            header_table = Table(header_data, colWidths=[6*cm, 13.6*cm])
            header_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ]))
            elements.append(header_table)
        except Exception:
            elements.append(Paragraph(copyright_text_content, copyright_style))
    else:
        elements.append(Paragraph(copyright_text_content, copyright_style))
    elements.append(Spacer(1, 2*mm))
    
    # ==================== 报告标题 ====================
    title_text = f"{project_name} Report"
    if len(title_text) > 60:
        dynamic_title_font_size = 11 if sp['label_font'] <= 8 else 12
    elif len(title_text) > 45:
        dynamic_title_font_size = 13 if sp['label_font'] <= 8 else 14
    else:
        dynamic_title_font_size = 15 if sp['label_font'] <= 8 else 16
    
    dynamic_title_style = ParagraphStyle(
        'DynamicTitleStyle', parent=styles['Normal'],
        fontName=font_name, fontSize=dynamic_title_font_size, textColor=colors.black,
        alignment=TA_CENTER, spaceAfter=6, spaceBefore=3
    )
    elements.append(Paragraph(title_text, dynamic_title_style))
    elements.append(Spacer(1, sp['spacer_after_title']*mm))

    # ==================== 封面表格 ====================
    total_cases = sum(r.get('test_cases', 0) for r in test_results)
    total_pass = sum(r.get('pass', 0) for r in test_results)
    total_passing_rate = (total_pass / total_cases * 100) if total_cases > 0 else 0
    
    conclusion_text, release_criteria = get_conclusion_and_criteria(
        template_config, total_passing_rate, zmind_stats,
        has_zmind_csv, include_pr_closed, html_escape=True
    )
    
    cover_rows_with_keys = [
        (None, '项目名称<br/>Project name', _safe_text(project_name)),
        ('test_cycle', '测试周期<br/>Test Cycle', _safe_text(report_data.get('test_cycle', ''))),
        ('testers', '测试人员<br/>Testers', _safe_text(report_data.get('testers', ''))),
        ('reviewer_name', '审核人员<br/>Reviewer', _safe_text(report_data.get('reviewer_name', ''))),
        (None, '验证环境<br/>Verified environment', _safe_text((report_data.get('verify_env', '') or '').replace('\n', '<br/>'))),
        (None, '提测内容<br/>Release Note', _safe_text((report_data.get('release_note', '') or '').replace('\n', '<br/>'))),
        ('test_conclusion', '测试结论<br/>Test Conclusion', conclusion_text),
        ('release_criteria', '测试通过标准<br/>Release Criteria', release_criteria),
        (None, '风险评估<br/>Risk Assessment', _safe_text((report_data.get('risk_assessment', '') or '').replace('\n', '<br/>'))),
        ('remark', '备注<br/>Remark', _safe_text((report_data.get('report_remark', '') or '').replace('\n', '<br/>'))),
    ]
    cover_rows = filter_cover_rows(cover_rows_with_keys, selected_fields)
    
    cover_data = []
    for label, value in cover_rows:
        cover_data.append([
            Paragraph(f"<b>{label}</b>", label_style),
            Paragraph(str(value), content_style)
        ])
    
    cover_table = Table(cover_data, colWidths=[5*cm, 14.6*cm])
    cover_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('BACKGROUND', (0, 0), (0, -1), orange_bg),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), sp['cover_padding']),
        ('BOTTOMPADDING', (0, 0), (-1, -1), sp['cover_padding']),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('GRID', (0, 0), (-1, -1), 1, black_border_color),
    ]))
    elements.append(cover_table)
    elements.append(Spacer(1, sp['spacer_after_cover']*mm))

    # ==================== 分页：Test Result Detail（按模板 selected_fields 控制） ====================
    if is_field_visible(selected_fields, 'test_results'):

        # 检测是否有协测列
        has_assist = report_data.get('has_assist', False)
        if not has_assist:
            has_assist = any(r.get('assist', 0) > 0 for r in test_results)

        # ==================== Test Result Detail 标题 ====================
        total_table_width = 19.6*cm
        section_data = [[Paragraph("<b>Test Result Detail</b>", section_title_style)]]
        section_table = Table(section_data, colWidths=[total_table_width])
        section_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), light_gray_bg),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), sp['section_padding']),
            ('BOTTOMPADDING', (0, 0), (-1, -1), sp['section_padding']),
        ]))
        elements.append(section_table)
        
        # ==================== Test Result Detail 表格 ====================
        if has_assist:
            result_header = [
                Paragraph("<b>Module</b>", table_cell_style),
                Paragraph("<b>TestCases</b>", table_cell_style),
                Paragraph("<b>PASS</b>", table_cell_style),
                Paragraph("<b>FAIL</b>", table_cell_style),
                Paragraph("<b>BLOCK</b>", table_cell_style),
                Paragraph("<b>NT</b>", table_cell_style),
                Paragraph("<b>NA</b>", table_cell_style),
                Paragraph("<b>协测</b>", table_cell_style),
                Paragraph("<b>Passing rate</b>", table_cell_style),
            ]
            col_widths = [4.6*cm, 2*cm, 1.5*cm, 1.5*cm, 1.5*cm, 1.5*cm, 1.5*cm, 1.5*cm, 4*cm]
        else:
            result_header = [
                Paragraph("<b>Module</b>", table_cell_style),
                Paragraph("<b>TestCases</b>", table_cell_style),
                Paragraph("<b>PASS</b>", table_cell_style),
                Paragraph("<b>FAIL</b>", table_cell_style),
                Paragraph("<b>BLOCK</b>", table_cell_style),
                Paragraph("<b>NT</b>", table_cell_style),
                Paragraph("<b>NA</b>", table_cell_style),
                Paragraph("<b>Passing rate</b>", table_cell_style),
            ]
            col_widths = [5*cm, 2*cm, 1.5*cm, 1.5*cm, 1.5*cm, 1.5*cm, 1.5*cm, 5.1*cm]
        result_data = [result_header]
        
        t_cases = 0
        t_pass = 0
        t_fail = 0
        t_block = 0
        t_nt = 0
        t_na = 0
        t_assist = 0
        
        for result in test_results:
            tc = result.get('test_cases', 0)
            ps = result.get('pass', 0)
            fl = result.get('fail', 0)
            bk = result.get('block', 0)
            nt = result.get('nt', 0)
            na = result.get('na', 0)
            ast = result.get('assist', 0)
            pr = (ps / tc * 100) if tc > 0 else 0
            
            row = [
                Paragraph(_safe_text(result.get('module', '')), table_cell_style),
                Paragraph(str(tc), table_cell_style),
                Paragraph(str(ps), table_cell_style),
                Paragraph(str(fl), table_cell_style),
                Paragraph(str(bk), table_cell_style),
                Paragraph(str(nt), table_cell_style),
                Paragraph(str(na), table_cell_style),
            ]
            if has_assist:
                row.append(Paragraph(str(ast), table_cell_style))
            row.append(Paragraph(f"{pr:.2f}%", table_cell_style))
            result_data.append(row)
            t_cases += tc
            t_pass += ps
            t_fail += fl
            t_block += bk
            t_nt += nt
            t_na += na
            t_assist += ast
        
        # Total行
        total_pr = (t_pass / t_cases * 100) if t_cases > 0 else 0
        total_row = [
            Paragraph("<b>Total</b>", table_cell_style),
            Paragraph(f"<b>{t_cases}</b>", table_cell_style),
            Paragraph(f"<b>{t_pass}</b>", table_cell_style),
            Paragraph(f"<b>{t_fail}</b>", table_cell_style),
            Paragraph(f"<b>{t_block}</b>", table_cell_style),
            Paragraph(f"<b>{t_nt}</b>", table_cell_style),
            Paragraph(f"<b>{t_na}</b>", table_cell_style),
        ]
        if has_assist:
            total_row.append(Paragraph(f"<b>{t_assist}</b>", table_cell_style))
        total_row.append(Paragraph(f"<b>{total_pr:.2f}%</b>", table_cell_style))
        result_data.append(total_row)
        
        # Test Case Passed行
        total_executed = t_cases
        pass_pct = (t_pass / total_executed * 100) if total_executed > 0 else 0
        fail_pct = (t_fail / total_executed * 100) if total_executed > 0 else 0
        block_pct = (t_block / total_executed * 100) if total_executed > 0 else 0
        nt_pct = (t_nt / total_executed * 100) if total_executed > 0 else 0
        ok_ng = 'OK' if total_pr >= 95 else 'NG'

        # OK/NG单元格样式
        ok_ng_color = colors.Color(0.18, 0.49, 0.20) if ok_ng == 'OK' else colors.Color(0.78, 0.16, 0.16)
        ok_ng_bg = colors.Color(0.91, 0.96, 0.91) if ok_ng == 'OK' else colors.Color(1.0, 0.92, 0.93)
        ok_ng_style = ParagraphStyle(
            'OkNgStyle', parent=styles['Normal'],
            fontName=font_name, fontSize=sp['okng_font'], textColor=ok_ng_color,
            alignment=TA_CENTER
        )

        passed_row = [
            Paragraph("<b>Test Case Passed</b>", table_cell_style),
        ]
        if has_assist:
            passed_row.extend([
                Paragraph(f"<b>{pass_pct + fail_pct + block_pct + nt_pct:.2f}%</b>", table_cell_style),
                Paragraph(f"<b>{pass_pct:.2f}%</b>", table_cell_style),
                Paragraph(f"<b>{fail_pct:.2f}%</b>", table_cell_style),
                Paragraph(f"<b>{block_pct:.2f}%</b>", table_cell_style),
                Paragraph(f"<b>{nt_pct:.2f}%</b>", table_cell_style),
                Paragraph("", table_cell_style),
                Paragraph("", table_cell_style),
                Paragraph(f"<b>{ok_ng}</b>", ok_ng_style),
            ])
        else:
            passed_row.extend([
                Paragraph(f"<b>{pass_pct + fail_pct + block_pct + nt_pct:.2f}%</b>", table_cell_style),
                Paragraph(f"<b>{pass_pct:.2f}%</b>", table_cell_style),
                Paragraph(f"<b>{fail_pct:.2f}%</b>", table_cell_style),
                Paragraph(f"<b>{block_pct:.2f}%</b>", table_cell_style),
                Paragraph(f"<b>{nt_pct:.2f}%</b>", table_cell_style),
                Paragraph("", table_cell_style),
                Paragraph(f"<b>{ok_ng}</b>", ok_ng_style),
            ])
        result_data.append(passed_row)
        
        num_data_rows = len(test_results)
        num_cols = 9 if has_assist else 8
        total_rows = num_data_rows + 3  # header + data + Total + Passed
        passed_row_idx = num_data_rows + 2  # header(0) + data rows + Total row
        
        result_table = Table(result_data, colWidths=col_widths)
        
        result_style = [
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, black_border_color),
            ('TOPPADDING', (0, 0), (-1, -1), sp['cell_padding']),
            ('BOTTOMPADDING', (0, 0), (-1, -1), sp['cell_padding']),
            # 表头灰色背景
            ('BACKGROUND', (0, 0), (-1, 0), gray_bg),
            # OK/NG单元格背景色
            ('BACKGROUND', (num_cols - 1, passed_row_idx), (num_cols - 1, passed_row_idx), ok_ng_bg),
            # Module列（第一列）灰色背景（数据行+Total+Passed）
        ]
        for i in range(1, total_rows):
            result_style.append(('BACKGROUND', (0, i), (0, i), gray_bg))
        
        result_table.setStyle(TableStyle(result_style))
        elements.append(result_table)
        elements.append(Spacer(1, sp['spacer_after_result']*mm))
        
        # 测试结果说明
        note_table_data = [[Paragraph(
            "测试结果说明：Pass-测试通过；Fail-测试失败；NT-暂未测试；NA-不适用；",
            note_style
        )]]
        note_table = Table(note_table_data, colWidths=[total_table_width])
        note_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(note_table)
        elements.append(Spacer(1, sp['spacer_after_note']*mm))

    # ==================== Zmind-PR 表格（按模板 selected_fields 控制） ====================
    if is_field_visible(selected_fields, 'zmind_stats') and has_zmind_csv and zmind_stats:
        zmind_header = [
            Paragraph("<b>Zmind-PR</b>", table_cell_style),
            Paragraph("<b>PRs</b>", table_cell_style),
            Paragraph("<b>Blocker</b>", table_cell_style),
            Paragraph("<b>Critical</b>", table_cell_style),
            Paragraph("<b>Major</b>", table_cell_style),
            Paragraph("<b>Minor</b>", table_cell_style),
            Paragraph("<b>Enhancement</b>", table_cell_style),
            Paragraph("<b>Conclusion</b>", table_cell_style),
        ]
        
        total_prs = zmind_stats.get('total_prs', 0)
        blocker = zmind_stats.get('blocker', 0)
        critical = zmind_stats.get('critical', 0)
        major = zmind_stats.get('major', 0)
        minor = zmind_stats.get('minor', 0)
        enhancement = zmind_stats.get('enhancement', 0)
        
        open_blocker = zmind_stats.get('open_blocker', 0)
        open_critical = zmind_stats.get('open_critical', 0)
        open_major = zmind_stats.get('open_major', 0)
        open_minor = zmind_stats.get('open_minor', 0)
        open_enhancement = zmind_stats.get('open_enhancement', 0)
        open_count = open_blocker + open_critical + open_major + open_minor + open_enhancement
        
        blocker_cr = ((blocker - open_blocker) / blocker * 100) if blocker > 0 else 100
        critical_cr = ((critical - open_critical) / critical * 100) if critical > 0 else 100
        major_cr = ((major - open_major) / major * 100) if major > 0 else 100
        
        zmind_conclusion = get_zmind_conclusion(template_config, zmind_stats, include_pr_closed)
        
        conclusion_color = colors.Color(0.18, 0.49, 0.20) if zmind_conclusion == 'OK' else colors.Color(0.78, 0.16, 0.16)
        conclusion_bg = colors.Color(0.91, 0.96, 0.91) if zmind_conclusion == 'OK' else colors.Color(1.0, 0.92, 0.93)
        
        zmind_data = [zmind_header]
        
        # Open行
        zmind_data.append([
            Paragraph("Open", table_cell_style),
            Paragraph(str(open_count), table_cell_style),
            Paragraph(str(open_blocker), table_cell_style),
            Paragraph(str(open_critical), table_cell_style),
            Paragraph(str(open_major), table_cell_style),
            Paragraph(str(open_minor), table_cell_style),
            Paragraph(str(open_enhancement), table_cell_style),
            Paragraph("", table_cell_style),  # Conclusion通过合并单元格显示
        ])
        
        if include_pr_closed:
            # Total行
            zmind_data.append([
                Paragraph("<b>Total</b>", table_cell_style),
                Paragraph(f"<b>{total_prs}</b>", table_cell_style),
                Paragraph(f"<b>{blocker}</b>", table_cell_style),
                Paragraph(f"<b>{critical}</b>", table_cell_style),
                Paragraph(f"<b>{major}</b>", table_cell_style),
                Paragraph(f"<b>{minor}</b>", table_cell_style),
                Paragraph(f"<b>{enhancement}</b>", table_cell_style),
                Paragraph("", table_cell_style),
            ])
            
            # PR closed行
            closed_rate = ((total_prs - open_count) / total_prs * 100) if total_prs > 0 else 100
            minor_cr = ((minor - open_minor) / minor * 100) if minor > 0 else 100
            enhancement_cr = ((enhancement - open_enhancement) / enhancement * 100) if enhancement > 0 else 100
            
            zmind_data.append([
                Paragraph("<b>PR closed</b>", table_cell_style),
                Paragraph(f"<b>{closed_rate:.2f}%</b>", table_cell_style),
                Paragraph(f"<b>{blocker_cr:.2f}%</b>", table_cell_style),
                Paragraph(f"<b>{critical_cr:.2f}%</b>", table_cell_style),
                Paragraph(f"<b>{major_cr:.2f}%</b>", table_cell_style),
                Paragraph(f"<b>{minor_cr:.2f}%</b>", table_cell_style),
                Paragraph(f"<b>{enhancement_cr:.2f}%</b>", table_cell_style),
                Paragraph("", table_cell_style),
            ])
        
        zmind_row_count = 1 if not include_pr_closed else 3
        
        # 调整列宽使总宽度与Test Result Detail表格一致（19cm）
        zmind_col_widths = [2.8*cm, 2.2*cm, 2.2*cm, 2.2*cm, 2.2*cm, 2.2*cm, 2.8*cm, 3*cm]
        zmind_table = Table(zmind_data, colWidths=zmind_col_widths)
        
        zmind_style_list = [
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, black_border_color),
            ('TOPPADDING', (0, 0), (-1, -1), sp['cell_padding']),
            ('BOTTOMPADDING', (0, 0), (-1, -1), sp['cell_padding']),
            # 表头灰色背景
            ('BACKGROUND', (0, 0), (-1, 0), gray_bg),
            # Zmind-PR列灰色背景
        ]
        for i in range(1, zmind_row_count + 1):
            zmind_style_list.append(('BACKGROUND', (0, i), (0, i), gray_bg))
        
        # 合并Conclusion列
        if zmind_row_count > 1:
            zmind_style_list.append(('SPAN', (7, 1), (7, zmind_row_count)))
        
        # Conclusion单元格背景色
        zmind_style_list.append(('BACKGROUND', (7, 1), (7, zmind_row_count), conclusion_bg))
        
        zmind_table.setStyle(TableStyle(zmind_style_list))
        
        # 在Conclusion合并单元格中写入值（直接修改第一个数据行的第8列）
        conclusion_cell_style = ParagraphStyle(
            'ConclusionStyle', parent=styles['Normal'],
            fontName=font_name, fontSize=sp['conclusion_font'], textColor=conclusion_color,
            alignment=TA_CENTER
        )
        zmind_data[1][7] = Paragraph(f"<b>{zmind_conclusion}</b>", conclusion_cell_style)
        
        # 重新创建表格（因为修改了数据）
        zmind_table = Table(zmind_data, colWidths=zmind_col_widths)
        zmind_table.setStyle(TableStyle(zmind_style_list))
        
        elements.append(zmind_table)
        elements.append(Spacer(1, sp['spacer_after_zmind']*mm))
        
        # Severity说明 - 使用表格包装以保持与上方表格对齐
        severity_note_data = [[Paragraph(
            "Severity：Blocker-致命性或阻塞进度的问题；Critical－关键功能及稳定性问题；Major－次要功能问题；Minor-界面或优化问题；Enhancement-增强建议",
            note_style
        )]]
        severity_note_table = Table(severity_note_data, colWidths=[19.6*cm])
        severity_note_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(severity_note_table)
    
    # ==================== Issue列表（按模板 selected_fields 控制） ====================
    if is_field_visible(selected_fields, 'issue_list') and issue_list:
        # Issue表格样式（准备数据，稍后在用例表格后面添加）
        issue_cell_style = ParagraphStyle(
            'IssueCellStyle', parent=styles['Normal'],
            fontName=font_name, fontSize=7, textColor=colors.black,
            alignment=TA_CENTER
        )
        issue_cell_left = ParagraphStyle(
            'IssueCellLeft', parent=styles['Normal'],
            fontName=font_name, fontSize=7, textColor=colors.black,
            alignment=TA_LEFT
        )
        
        # Severity颜色映射
        severity_colors = {
            'blocker': colors.Color(0.96, 0.42, 0.42),  # #f56c6c
            'critical': colors.Color(0.90, 0.64, 0.24),  # #e6a23c
            'major': colors.Color(0.25, 0.62, 1.0),      # #409eff
            'minor': colors.Color(0.40, 0.76, 0.23),     # #67c23a
            'enhancement': colors.Color(0.56, 0.64, 0.60) # #909399
        }
        
        # 状态颜色映射
        from utils.constants import OPEN_STATUS_ORDER
        open_statuses = OPEN_STATUS_ORDER
        
        issue_header = [
            Paragraph("<b>#(PR号)</b>", issue_cell_style),
            Paragraph("<b>跟踪</b>", issue_cell_style),
            Paragraph("<b>类别</b>", issue_cell_style),
            Paragraph("<b>Severity</b>", issue_cell_style),
            Paragraph("<b>状态</b>", issue_cell_style),
            Paragraph("<b>优先级</b>", issue_cell_style),
            Paragraph("<b>主题</b>", issue_cell_style),
            Paragraph("<b>指派给</b>", issue_cell_style),
        ]
        issue_data = [issue_header]
        
        for issue in issue_list:
            severity = issue.get('severity', '') or ''
            severity_lower = severity.lower()
            severity_color = severity_colors.get(severity_lower, colors.black)
            
            status = issue.get('status', '') or ''
            status_color = colors.Color(0.96, 0.42, 0.42) if status in open_statuses else colors.Color(0.40, 0.76, 0.23)
            
            severity_style = ParagraphStyle(
                'SeverityStyle', parent=issue_cell_style,
                textColor=severity_color
            )
            status_style = ParagraphStyle(
                'StatusStyle', parent=issue_cell_style,
                textColor=status_color
            )
            
            # 主题完整显示，通过Paragraph自动换行
            subject = _safe_text(issue.get('subject', '') or '-')
            category = _safe_text(issue.get('category', '') or '-')
            assignee = _safe_text(issue.get('assignee', '') or '-')
            
            issue_data.append([
                Paragraph(_safe_text(str(issue.get('pr_number', '') or '-')), issue_cell_style),
                Paragraph(_safe_text(str(issue.get('tracker', '') or '-')), issue_cell_style),
                Paragraph(str(category), issue_cell_style),
                Paragraph(f"<b>{_safe_text(severity)}</b>" if severity else '-', severity_style),
                Paragraph(f"<b>{_safe_text(status)}</b>" if status else '-', status_style),
                Paragraph(_safe_text(str(issue.get('priority', '') or '-')), issue_cell_style),
                Paragraph(subject, issue_cell_left),
                Paragraph(str(assignee), issue_cell_style),
            ])
        
        issue_table = Table(issue_data, colWidths=[1.5*cm, 1.5*cm, 1.8*cm, 1.8*cm, 2*cm, 1.5*cm, 7.1*cm, 2.4*cm])
        
        issue_style = [
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (6, 1), (6, -1), 'LEFT'),  # 主题列左对齐
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, black_border_color),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('BACKGROUND', (0, 0), (-1, 0), gray_bg),
        ]
        issue_table.setStyle(TableStyle(issue_style))
        # Issue表格将在用例表格后面添加
    
    # ==================== 用例详细情况（按模板 selected_fields 控制） ====================
    if is_field_visible(selected_fields, 'test_cases') and test_cases:
        elements.append(PageBreak())
        
        # 用例表格小字体样式
        case_cell_style = ParagraphStyle(
            'CaseCellStyle', parent=styles['Normal'],
            fontName=font_name, fontSize=7, textColor=colors.black,
            alignment=TA_LEFT
        )
        case_cell_center = ParagraphStyle(
            'CaseCellCenter', parent=styles['Normal'],
            fontName=font_name, fontSize=7, textColor=colors.black,
            alignment=TA_CENTER
        )
        
        case_header = [
            Paragraph("<b>用例编号</b>", case_cell_center),
            Paragraph("<b>所属模块</b>", case_cell_center),
            Paragraph("<b>用例标题</b>", case_cell_center),
            Paragraph("<b>前置条件</b>", case_cell_center),
            Paragraph("<b>操作步骤</b>", case_cell_center),
            Paragraph("<b>预期结果</b>", case_cell_center),
            Paragraph("<b>用例等级</b>", case_cell_center),
            Paragraph("<b>测试结果</b>", case_cell_center),
            Paragraph("<b>执行备注</b>", case_cell_center),
        ]
        case_data = [case_header]
        
        result_map = {'PASS': 'PASS', 'FAIL': 'FAIL', 'BLOCK': 'BLOCK', 'NT': 'NT', 'NA': 'NA'}
        
        for tc in test_cases:
            case_data.append([
                Paragraph(_safe_text(tc.get('case_number', '')), case_cell_style),
                Paragraph(_safe_text(tc.get('module', '')), case_cell_style),
                Paragraph(_safe_text(tc.get('name', '')), case_cell_style),
                Paragraph(_safe_text(_truncate_text(tc.get('precondition', '').replace('\n', '<br/>'), 300)), case_cell_style),
                Paragraph(_safe_text(_truncate_text(tc.get('steps', '').replace('\n', '<br/>'), 300)), case_cell_style),
                Paragraph(_safe_text(_truncate_text(tc.get('expected_result', '').replace('\n', '<br/>'), 300)), case_cell_style),
                Paragraph(_safe_text(tc.get('level', '')), case_cell_center),
                Paragraph(result_map.get(tc.get('result', ''), tc.get('result', '')), case_cell_center),
                Paragraph(_safe_text(_truncate_text(tc.get('remark', ''), 300)), case_cell_style),
            ])
        
        # 9列：用例编号1.8, 模块1.5, 标题2.5, 前置条件1.8, 操作步骤3, 预期结果2.4, 等级1.5, 结果1.5, 备注2.7 = 19.7 → 调整
        case_table = Table(case_data, colWidths=[1.8*cm, 1.5*cm, 2.5*cm, 1.8*cm, 3.5*cm, 2.5*cm, 1.5*cm, 1.5*cm, 3*cm])
        
        case_style = [
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, black_border_color),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('BACKGROUND', (0, 0), (-1, 0), gray_bg),
        ]
        case_table.setStyle(TableStyle(case_style))
        elements.append(case_table)
    
    # ==================== Issue列表（放在用例表格后面，按模板 selected_fields 控制） ====================
    if is_field_visible(selected_fields, 'issue_list') and issue_list:
        elements.append(Spacer(1, 8*mm))
        
        # Issue List标题
        issue_section_data2 = [[Paragraph("<b>Issue List</b>", section_title_style)]]
        issue_section_table2 = Table(issue_section_data2, colWidths=[19.6*cm])
        issue_section_table2.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), light_gray_bg),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(issue_section_table2)
        elements.append(issue_table)
    
    # 生成PDF
    doc.build(elements)
    return output_path


def generate_report_pdf_stream(report_data, test_results, zmind_stats, test_cases, issue_list=None, mplist_data=None, progress_callback=None):
    """
    生成测试报告PDF到内存流，不保存到文件
    
    Args:
        report_data: 报告基本信息
        test_results: 测试结果列表
        zmind_stats: Zmind统计信息字典
        test_cases: 用例详细列表
        issue_list: Issue列表
        mplist_data: MpList数据列表
    
    Returns:
        BytesIO: PDF文件的内存流
    """
    import io
    
    logger.info(f"[PDF生成] 开始生成PDF, project_name: {report_data.get('project_name', '')}, test_results: {len(test_results)}条, test_cases: {len(test_cases)}条, issue_list: {len(issue_list or [])}条, mplist_data: {bool(mplist_data)}")
    
    if issue_list is None:
        issue_list = []
    if mplist_data is None:
        mplist_data = []
    
    font_name = register_chinese_font()
    
    stream = io.BytesIO()
    doc = SimpleDocTemplate(
        stream,
        pagesize=A4,
        rightMargin=7*mm,
        leftMargin=7*mm,
        topMargin=7*mm,
        bottomMargin=7*mm
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # ===== 预计算内容量，决定自适应样式参数 =====
    include_pr_closed = report_data.get('include_pr_closed', 0)
    has_zmind_csv = report_data.get('has_zmind_csv', False)
    
    template_config = report_data.get('report_template_config')
    selected_fields = get_selected_fields(template_config)
    
    _pre_cover_keys = [
        (None, '', ''),
        ('test_cycle', '', ''), ('testers', '', ''), ('reviewer_name', '', ''),
        (None, '', ''), (None, '', ''),
        ('test_conclusion', '', ''), ('release_criteria', '', ''),
        (None, '', ''), ('remark', '', ''),
    ]
    _pre_cover_rows = filter_cover_rows(_pre_cover_keys, selected_fields)
    cover_row_count = len(_pre_cover_rows)
    
    has_zmind_section = is_field_visible(selected_fields, 'zmind_stats') and has_zmind_csv and zmind_stats
    has_result_section = is_field_visible(selected_fields, 'test_results')
    result_module_count = len(test_results) if has_result_section else 0
    
    sp = _calc_first_page_style_params(cover_row_count, result_module_count, has_zmind_section, include_pr_closed)
    
    # ===== 样式定义（使用自适应参数） =====
    copyright_style = ParagraphStyle(
        'CopyrightStyle', parent=styles['Normal'],
        fontName=font_name, fontSize=sp['copyright_font'], textColor=colors.Color(0.4, 0.4, 0.4),
        alignment=TA_RIGHT
    )
    
    section_title_style = ParagraphStyle(
        'SectionTitleStyle', parent=styles['Normal'],
        fontName=font_name, fontSize=sp['section_font'], textColor=colors.black,
        alignment=TA_CENTER, leading=sp['section_font'] + 3
    )
    
    label_style = ParagraphStyle(
        'LabelStyle', parent=styles['Normal'],
        fontName=font_name, fontSize=sp['label_font'], textColor=colors.black,
        alignment=TA_CENTER, leading=sp['label_leading']
    )
    
    content_style = ParagraphStyle(
        'ContentStyle', parent=styles['Normal'],
        fontName=font_name, fontSize=sp['content_font'], textColor=colors.black,
        alignment=TA_LEFT, leading=sp['content_leading']
    )
    
    note_style = ParagraphStyle(
        'NoteStyle', parent=styles['Normal'],
        fontName=font_name, fontSize=sp['note_font'], textColor=colors.Color(0.4, 0.4, 0.4),
        alignment=TA_LEFT, leading=sp['cell_leading'], backColor=colors.Color(0.906, 0.902, 0.902)
    )
    
    table_cell_style = ParagraphStyle(
        'TableCellStyle', parent=styles['Normal'],
        fontName=font_name, fontSize=sp['cell_font'], textColor=colors.black,
        alignment=TA_CENTER, leading=sp['cell_leading']
    )
    
    # 颜色定义
    orange_bg = colors.Color(1, 0.8, 0.6)
    gray_bg = colors.Color(0.906, 0.902, 0.902)
    light_gray_bg = colors.Color(0.95, 0.95, 0.95)
    black_border_color = colors.black
    
    # ==================== Logo + 版权信息 ====================
    logo_path = report_data.get('logo_path', '')
    year = datetime.now().year
    
    if logo_path and os.path.exists(logo_path):
        try:
            logo = Image(logo_path, width=2.5*cm, height=0.75*cm)
            logo_table = Table(
                [[logo, Paragraph(f"Confidential &amp; Proprietary<br/>Copyright © {year} Whale TV Information Technology", copyright_style)]],
                colWidths=[3*cm, 16.6*cm]
            )
            logo_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ]))
            elements.append(logo_table)
        except Exception:
            elements.append(Paragraph(f"Confidential &amp; Proprietary<br/>Copyright © {year} Whale TV Information Technology", copyright_style))
    else:
        elements.append(Paragraph(f"Confidential &amp; Proprietary<br/>Copyright © {year} Whale TV Information Technology", copyright_style))
    
    elements.append(Spacer(1, 2*mm))
    
    # ==================== 报告标题 ====================
    project_name = report_data.get('project_name', '')
    # 根据标题长度动态调整字体大小
    title_text = f"{project_name} Report"
    if len(title_text) > 60:
        dynamic_title_font_size = 11 if sp['label_font'] <= 8 else 12
    elif len(title_text) > 45:
        dynamic_title_font_size = 13 if sp['label_font'] <= 8 else 14
    else:
        dynamic_title_font_size = 15 if sp['label_font'] <= 8 else 16
    
    dynamic_title_style = ParagraphStyle(
        'DynamicTitleStyle', parent=styles['Normal'],
        fontName=font_name, fontSize=dynamic_title_font_size, textColor=colors.black,
        alignment=TA_CENTER, spaceAfter=6, spaceBefore=3
    )
    elements.append(Paragraph(f"<b>{title_text}</b>", dynamic_title_style))
    elements.append(Spacer(1, sp['spacer_after_title']*mm))
    
    # ==================== 封面表格 ====================
    total_cases = sum(r.get('test_cases', 0) for r in test_results)
    total_pass = sum(r.get('pass', 0) for r in test_results)
    total_passing_rate = (total_pass / total_cases * 100) if total_cases > 0 else 0
    
    conclusion, release_criteria = get_conclusion_and_criteria(
        template_config, total_passing_rate, zmind_stats,
        has_zmind_csv, include_pr_closed, html_escape=True
    )
    
    cover_rows_with_keys = [
        (None, '项目名称<br/>Project name', _safe_text(report_data.get('project_name', ''))),
        ('test_cycle', '测试周期<br/>Test Cycle', _safe_text(report_data.get('test_cycle', ''))),
        ('testers', '测试人员<br/>Testers', _safe_text(report_data.get('testers', ''))),
        ('reviewer_name', '审核人员<br/>Reviewer', _safe_text(report_data.get('reviewer_name', ''))),
        (None, '验证环境<br/>Verified environment', _safe_text((report_data.get('verify_env', '') or '').replace('\n', '<br/>'))),
        (None, '提测内容<br/>Release Note', _safe_text((report_data.get('release_note', '') or '').replace('\n', '<br/>'))),
        ('test_conclusion', '测试结论<br/>Test Conclusion', conclusion),
        ('release_criteria', '测试通过标准<br/>Release Criteria', release_criteria),
        (None, '风险评估<br/>Risk Assessment', _safe_text((report_data.get('risk_assessment', '') or '').replace('\n', '<br/>'))),
        ('remark', '备注<br/>Remark', _safe_text((report_data.get('report_remark', '') or '').replace('\n', '<br/>'))),
    ]
    cover_rows = filter_cover_rows(cover_rows_with_keys, selected_fields)
    
    cover_data = []
    for label, value in cover_rows:
        cover_data.append([
            Paragraph(f"<b>{label}</b>", label_style),
            Paragraph(str(value), content_style)
        ])
    
    cover_table = Table(cover_data, colWidths=[4.5*cm, 15.1*cm])
    cover_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 1, black_border_color),
        ('BACKGROUND', (0, 0), (0, -1), orange_bg),
        ('TOPPADDING', (0, 0), (-1, -1), sp['cover_padding']),
        ('BOTTOMPADDING', (0, 0), (-1, -1), sp['cover_padding']),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(cover_table)
    elements.append(Spacer(1, sp['spacer_after_cover']*mm))
    
    # ==================== Test Result Detail（按模板 selected_fields 控制） ====================
    if is_field_visible(selected_fields, 'test_results'):
        
        # 检测是否有协测列
        has_assist = report_data.get('has_assist', False)
        if not has_assist:
            has_assist = any(r.get('assist', 0) > 0 for r in test_results)
        
        total_table_width = 19.6*cm
        
        section_table = Table([[Paragraph("<b>Test Result Detail</b>", section_title_style)]], colWidths=[total_table_width])
        section_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), light_gray_bg),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), sp['section_padding']),
            ('BOTTOMPADDING', (0, 0), (-1, -1), sp['section_padding']),
        ]))
        elements.append(section_table)
    
        # 表头
        if has_assist:
            result_header = [
                Paragraph("<b>Module</b>", table_cell_style),
                Paragraph("<b>TestCases</b>", table_cell_style),
                Paragraph("<b>PASS</b>", table_cell_style),
                Paragraph("<b>FAIL</b>", table_cell_style),
                Paragraph("<b>BLOCK</b>", table_cell_style),
                Paragraph("<b>NT</b>", table_cell_style),
                Paragraph("<b>NA</b>", table_cell_style),
                Paragraph("<b>协测</b>", table_cell_style),
                Paragraph("<b>Passing rate</b>", table_cell_style),
            ]
            col_widths = [4.6*cm, 2*cm, 1.5*cm, 1.5*cm, 1.5*cm, 1.5*cm, 1.5*cm, 1.5*cm, 4*cm]
        else:
            result_header = [
                Paragraph("<b>Module</b>", table_cell_style),
                Paragraph("<b>TestCases</b>", table_cell_style),
                Paragraph("<b>PASS</b>", table_cell_style),
                Paragraph("<b>FAIL</b>", table_cell_style),
                Paragraph("<b>BLOCK</b>", table_cell_style),
                Paragraph("<b>NT</b>", table_cell_style),
                Paragraph("<b>NA</b>", table_cell_style),
                Paragraph("<b>Passing rate</b>", table_cell_style),
            ]
            col_widths = [5*cm, 2*cm, 1.5*cm, 1.5*cm, 1.5*cm, 1.5*cm, 1.5*cm, 5.1*cm]
        result_data = [result_header]
        
        t_cases = 0
        t_pass = 0
        t_fail = 0
        t_block = 0
        t_nt = 0
        t_na = 0
        t_assist = 0
        
        for result in test_results:
            tc = result.get('test_cases', 0)
            ps = result.get('pass', 0)
            fl = result.get('fail', 0)
            bk = result.get('block', 0)
            nt = result.get('nt', 0)
            na = result.get('na', 0)
            ast = result.get('assist', 0)
            pr_str = result.get('passing_rate', '')
            if not pr_str:
                pr = (ps / tc * 100) if tc > 0 else 0
                pr_str = f'{pr:.2f}%'
            elif not pr_str.endswith('%'):
                pr_str = f'{float(pr_str) * 100:.2f}%'
            
            row = [
                Paragraph(_safe_text(result.get('module', '')), table_cell_style),
                Paragraph(str(tc), table_cell_style),
                Paragraph(str(ps), table_cell_style),
                Paragraph(str(fl), table_cell_style),
                Paragraph(str(bk), table_cell_style),
                Paragraph(str(nt), table_cell_style),
                Paragraph(str(na), table_cell_style),
            ]
            if has_assist:
                row.append(Paragraph(str(ast), table_cell_style))
            row.append(Paragraph(pr_str, table_cell_style))
            result_data.append(row)
            
            t_cases += tc
            t_pass += ps
            t_fail += fl
            t_block += bk
            t_nt += nt
            t_na += na
            t_assist += ast
        
        # Total行
        total_pr = (t_pass / t_cases * 100) if t_cases > 0 else 0
        total_row = [
            Paragraph("<b>Total</b>", table_cell_style),
            Paragraph(f"<b>{t_cases}</b>", table_cell_style),
            Paragraph(f"<b>{t_pass}</b>", table_cell_style),
            Paragraph(f"<b>{t_fail}</b>", table_cell_style),
            Paragraph(f"<b>{t_block}</b>", table_cell_style),
            Paragraph(f"<b>{t_nt}</b>", table_cell_style),
            Paragraph(f"<b>{t_na}</b>", table_cell_style),
        ]
        if has_assist:
            total_row.append(Paragraph(f"<b>{t_assist}</b>", table_cell_style))
        total_row.append(Paragraph(f"<b>{total_pr:.2f}%</b>", table_cell_style))
        result_data.append(total_row)
        
        # Test Case Passed行
        total_executed = t_cases
        pass_pct = (t_pass / total_executed * 100) if total_executed > 0 else 0
        fail_pct = (t_fail / total_executed * 100) if total_executed > 0 else 0
        block_pct = (t_block / total_executed * 100) if total_executed > 0 else 0
        nt_pct = (t_nt / total_executed * 100) if total_executed > 0 else 0
        ok_ng = 'OK' if total_pr >= 95 else 'NG'

        # OK/NG单元格样式
        ok_ng_color = colors.Color(0.18, 0.49, 0.20) if ok_ng == 'OK' else colors.Color(0.78, 0.16, 0.16)
        ok_ng_bg = colors.Color(0.91, 0.96, 0.91) if ok_ng == 'OK' else colors.Color(1.0, 0.92, 0.93)
        ok_ng_style = ParagraphStyle(
            'OkNgStyle2', parent=styles['Normal'],
            fontName=font_name, fontSize=sp['okng_font'], textColor=ok_ng_color,
            alignment=TA_CENTER
        )

        passed_row = [
            Paragraph("<b>Test Case Passed</b>", table_cell_style),
        ]
        if has_assist:
            passed_row.extend([
                Paragraph(f"<b>{pass_pct + fail_pct + block_pct + nt_pct:.2f}%</b>", table_cell_style),
                Paragraph(f"<b>{pass_pct:.2f}%</b>", table_cell_style),
                Paragraph(f"<b>{fail_pct:.2f}%</b>", table_cell_style),
                Paragraph(f"<b>{block_pct:.2f}%</b>", table_cell_style),
                Paragraph(f"<b>{nt_pct:.2f}%</b>", table_cell_style),
                Paragraph("", table_cell_style),
                Paragraph("", table_cell_style),
                Paragraph(f"<b>{ok_ng}</b>", ok_ng_style),
            ])
        else:
            passed_row.extend([
                Paragraph(f"<b>{pass_pct + fail_pct + block_pct + nt_pct:.2f}%</b>", table_cell_style),
                Paragraph(f"<b>{pass_pct:.2f}%</b>", table_cell_style),
                Paragraph(f"<b>{fail_pct:.2f}%</b>", table_cell_style),
                Paragraph(f"<b>{block_pct:.2f}%</b>", table_cell_style),
                Paragraph(f"<b>{nt_pct:.2f}%</b>", table_cell_style),
                Paragraph("", table_cell_style),
                Paragraph(f"<b>{ok_ng}</b>", ok_ng_style),
            ])
        result_data.append(passed_row)
        
        num_data_rows = len(test_results)
        num_cols = 9 if has_assist else 8
        total_rows = num_data_rows + 3
        passed_row_idx = num_data_rows + 2
        
        result_table = Table(result_data, colWidths=col_widths)
        
        result_style = [
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, black_border_color),
            ('TOPPADDING', (0, 0), (-1, -1), sp['cell_padding']),
            ('BOTTOMPADDING', (0, 0), (-1, -1), sp['cell_padding']),
            ('BACKGROUND', (0, 0), (-1, 0), gray_bg),
            # OK/NG单元格背景色
            ('BACKGROUND', (num_cols - 1, passed_row_idx), (num_cols - 1, passed_row_idx), ok_ng_bg),
        ]
        for i in range(1, len(result_data)):
            result_style.append(('BACKGROUND', (0, i), (0, i), gray_bg))
        
        result_table.setStyle(TableStyle(result_style))
        elements.append(result_table)
        elements.append(Spacer(1, sp['spacer_after_result']*mm))
        
        # 测试结果说明 - 使用表格包装以保持与上方表格对齐
        note_table_data = [[Paragraph(
            "测试结果说明：Pass-测试通过；Fail-测试失败；NT-暂未测试；NA-不适用；",
            note_style
        )]]
        note_table = Table(note_table_data, colWidths=[total_table_width])
        note_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(note_table)
        elements.append(Spacer(1, sp['spacer_after_note']*mm))

    # ==================== Zmind-PR 表格（按模板 selected_fields 控制） ====================
    if is_field_visible(selected_fields, 'zmind_stats') and has_zmind_csv and zmind_stats:
        zmind_header = [
            Paragraph("<b>Zmind-PR</b>", table_cell_style),
            Paragraph("<b>PRs</b>", table_cell_style),
            Paragraph("<b>Blocker</b>", table_cell_style),
            Paragraph("<b>Critical</b>", table_cell_style),
            Paragraph("<b>Major</b>", table_cell_style),
            Paragraph("<b>Minor</b>", table_cell_style),
            Paragraph("<b>Enhancement</b>", table_cell_style),
            Paragraph("<b>Conclusion</b>", table_cell_style),
        ]
        
        total_prs = zmind_stats.get('total_prs', 0)
        blocker = zmind_stats.get('blocker', 0)
        critical = zmind_stats.get('critical', 0)
        major = zmind_stats.get('major', 0)
        minor = zmind_stats.get('minor', 0)
        enhancement = zmind_stats.get('enhancement', 0)
        
        open_blocker = zmind_stats.get('open_blocker', 0)
        open_critical = zmind_stats.get('open_critical', 0)
        open_major = zmind_stats.get('open_major', 0)
        open_minor = zmind_stats.get('open_minor', 0)
        open_enhancement = zmind_stats.get('open_enhancement', 0)
        open_count = open_blocker + open_critical + open_major + open_minor + open_enhancement
        
        blocker_cr = ((blocker - open_blocker) / blocker * 100) if blocker > 0 else 100
        critical_cr = ((critical - open_critical) / critical * 100) if critical > 0 else 100
        major_cr = ((major - open_major) / major * 100) if major > 0 else 100
        
        zmind_conclusion = get_zmind_conclusion(template_config, zmind_stats, include_pr_closed)
        
        conclusion_color = colors.Color(0.18, 0.49, 0.20) if zmind_conclusion == 'OK' else colors.Color(0.78, 0.16, 0.16)
        conclusion_bg = colors.Color(0.91, 0.96, 0.91) if zmind_conclusion == 'OK' else colors.Color(1.0, 0.92, 0.93)
        
        zmind_data = [zmind_header]
        
        zmind_data.append([
            Paragraph("Open", table_cell_style),
            Paragraph(str(open_count), table_cell_style),
            Paragraph(str(open_blocker), table_cell_style),
            Paragraph(str(open_critical), table_cell_style),
            Paragraph(str(open_major), table_cell_style),
            Paragraph(str(open_minor), table_cell_style),
            Paragraph(str(open_enhancement), table_cell_style),
            Paragraph("", table_cell_style),
        ])
        
        if include_pr_closed:
            zmind_data.append([
                Paragraph("<b>Total</b>", table_cell_style),
                Paragraph(f"<b>{total_prs}</b>", table_cell_style),
                Paragraph(f"<b>{blocker}</b>", table_cell_style),
                Paragraph(f"<b>{critical}</b>", table_cell_style),
                Paragraph(f"<b>{major}</b>", table_cell_style),
                Paragraph(f"<b>{minor}</b>", table_cell_style),
                Paragraph(f"<b>{enhancement}</b>", table_cell_style),
                Paragraph("", table_cell_style),
            ])
            
            closed_rate = ((total_prs - open_count) / total_prs * 100) if total_prs > 0 else 100
            minor_cr = ((minor - open_minor) / minor * 100) if minor > 0 else 100
            enhancement_cr = ((enhancement - open_enhancement) / enhancement * 100) if enhancement > 0 else 100
            
            zmind_data.append([
                Paragraph("<b>PR closed</b>", table_cell_style),
                Paragraph(f"<b>{closed_rate:.2f}%</b>", table_cell_style),
                Paragraph(f"<b>{blocker_cr:.2f}%</b>", table_cell_style),
                Paragraph(f"<b>{critical_cr:.2f}%</b>", table_cell_style),
                Paragraph(f"<b>{major_cr:.2f}%</b>", table_cell_style),
                Paragraph(f"<b>{minor_cr:.2f}%</b>", table_cell_style),
                Paragraph(f"<b>{enhancement_cr:.2f}%</b>", table_cell_style),
                Paragraph("", table_cell_style),
            ])
        
        zmind_row_count = 1 if not include_pr_closed else 3
        
        # 调整列宽使总宽度与Test Result Detail表格一致（19cm）
        zmind_col_widths = [2.8*cm, 2.2*cm, 2.2*cm, 2.2*cm, 2.2*cm, 2.2*cm, 2.8*cm, 3*cm]
        zmind_table = Table(zmind_data, colWidths=zmind_col_widths)
        
        zmind_style_list = [
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, black_border_color),
            ('TOPPADDING', (0, 0), (-1, -1), sp['cell_padding']),
            ('BOTTOMPADDING', (0, 0), (-1, -1), sp['cell_padding']),
            ('BACKGROUND', (0, 0), (-1, 0), gray_bg),
        ]
        for i in range(1, zmind_row_count + 1):
            zmind_style_list.append(('BACKGROUND', (0, i), (0, i), gray_bg))
        
        if zmind_row_count > 1:
            zmind_style_list.append(('SPAN', (7, 1), (7, zmind_row_count)))
        
        # Conclusion单元格背景色
        zmind_style_list.append(('BACKGROUND', (7, 1), (7, zmind_row_count), conclusion_bg))
        
        zmind_table.setStyle(TableStyle(zmind_style_list))
        
        conclusion_cell_style = ParagraphStyle(
            'ConclusionStyle', parent=styles['Normal'],
            fontName=font_name, fontSize=sp['conclusion_font'], textColor=conclusion_color,
            alignment=TA_CENTER
        )
        zmind_data[1][7] = Paragraph(f"<b>{zmind_conclusion}</b>", conclusion_cell_style)
        
        zmind_table = Table(zmind_data, colWidths=zmind_col_widths)
        zmind_table.setStyle(TableStyle(zmind_style_list))
        
        elements.append(zmind_table)
        elements.append(Spacer(1, sp['spacer_after_zmind']*mm))
        
        # Severity说明 - 使用表格包装以保持与上方表格对齐
        severity_note_data = [[Paragraph(
            "Severity：Blocker-致命性或阻塞进度的问题；Critical－关键功能及稳定性问题；Major－次要功能问题；Minor-界面或优化问题；Enhancement-增强建议",
            note_style
        )]]
        severity_note_table = Table(severity_note_data, colWidths=[19.6*cm])
        severity_note_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(severity_note_table)
    
    # ==================== Issue列表（准备数据，按模板 selected_fields 控制） ====================
    if is_field_visible(selected_fields, 'issue_list') and issue_list:
        # Issue表格样式
        issue_cell_style = ParagraphStyle(
            'IssueCellStyle', parent=styles['Normal'],
            fontName=font_name, fontSize=7, textColor=colors.black,
            alignment=TA_CENTER
        )
        issue_cell_left = ParagraphStyle(
            'IssueCellLeft', parent=styles['Normal'],
            fontName=font_name, fontSize=7, textColor=colors.black,
            alignment=TA_LEFT
        )
        
        # Severity颜色映射
        severity_colors = {
            'blocker': colors.Color(0.96, 0.42, 0.42),  # #f56c6c
            'critical': colors.Color(0.90, 0.64, 0.24),  # #e6a23c
            'major': colors.Color(0.25, 0.62, 1.0),      # #409eff
            'minor': colors.Color(0.40, 0.76, 0.23),     # #67c23a
            'enhancement': colors.Color(0.56, 0.64, 0.60) # #909399
        }
        
        # 状态颜色映射
        from utils.constants import OPEN_STATUS_ORDER
        open_statuses = OPEN_STATUS_ORDER
        
        issue_header = [
            Paragraph("<b>#(PR号)</b>", issue_cell_style),
            Paragraph("<b>跟踪</b>", issue_cell_style),
            Paragraph("<b>类别</b>", issue_cell_style),
            Paragraph("<b>Severity</b>", issue_cell_style),
            Paragraph("<b>状态</b>", issue_cell_style),
            Paragraph("<b>优先级</b>", issue_cell_style),
            Paragraph("<b>主题</b>", issue_cell_style),
            Paragraph("<b>指派给</b>", issue_cell_style),
        ]
        issue_data = [issue_header]
        
        for issue in issue_list:
            severity = issue.get('severity', '') or ''
            severity_lower = severity.lower()
            severity_color = severity_colors.get(severity_lower, colors.black)
            
            status = issue.get('status', '') or ''
            status_color = colors.Color(0.96, 0.42, 0.42) if status in open_statuses else colors.Color(0.40, 0.76, 0.23)
            
            severity_style = ParagraphStyle(
                'SeverityStyle', parent=issue_cell_style,
                textColor=severity_color
            )
            status_style = ParagraphStyle(
                'StatusStyle', parent=issue_cell_style,
                textColor=status_color
            )
            
            # 主题完整显示，通过Paragraph自动换行
            subject = _safe_text(issue.get('subject', '') or '-')
            category = _safe_text(issue.get('category', '') or '-')
            assignee = _safe_text(issue.get('assignee', '') or '-')
            
            issue_data.append([
                Paragraph(_safe_text(str(issue.get('pr_number', '') or '-')), issue_cell_style),
                Paragraph(_safe_text(str(issue.get('tracker', '') or '-')), issue_cell_style),
                Paragraph(str(category), issue_cell_style),
                Paragraph(f"<b>{_safe_text(severity)}</b>" if severity else '-', severity_style),
                Paragraph(f"<b>{_safe_text(status)}</b>" if status else '-', status_style),
                Paragraph(_safe_text(str(issue.get('priority', '') or '-')), issue_cell_style),
                Paragraph(subject, issue_cell_left),
                Paragraph(str(assignee), issue_cell_style),
            ])
        
        issue_table = Table(issue_data, colWidths=[1.5*cm, 1.5*cm, 1.8*cm, 1.8*cm, 2*cm, 1.5*cm, 7.1*cm, 2.4*cm])
        
        issue_style = [
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (6, 1), (6, -1), 'LEFT'),  # 主题列左对齐
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, black_border_color),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('BACKGROUND', (0, 0), (-1, 0), gray_bg),
        ]
        issue_table.setStyle(TableStyle(issue_style))
        # Issue表格将在用例表格后面添加
    
    # ==================== 用例详细情况（按模板 selected_fields 控制） ====================
    if is_field_visible(selected_fields, 'test_cases') and test_cases:
        elements.append(PageBreak())
        
        case_cell_style = ParagraphStyle(
            'CaseCellStyle', parent=styles['Normal'],
            fontName=font_name, fontSize=7, textColor=colors.black,
            alignment=TA_LEFT
        )
        case_cell_center = ParagraphStyle(
            'CaseCellCenter', parent=styles['Normal'],
            fontName=font_name, fontSize=7, textColor=colors.black,
            alignment=TA_CENTER
        )
        
        case_header = [
            Paragraph("<b>用例编号</b>", case_cell_center),
            Paragraph("<b>所属模块</b>", case_cell_center),
            Paragraph("<b>用例标题</b>", case_cell_center),
            Paragraph("<b>前置条件</b>", case_cell_center),
            Paragraph("<b>操作步骤</b>", case_cell_center),
            Paragraph("<b>预期结果</b>", case_cell_center),
            Paragraph("<b>用例等级</b>", case_cell_center),
            Paragraph("<b>测试结果</b>", case_cell_center),
            Paragraph("<b>执行备注</b>", case_cell_center),
        ]
        case_data = [case_header]
        
        result_map = {'PASS': 'PASS', 'FAIL': 'FAIL', 'BLOCK': 'BLOCK', 'NT': 'NT', 'NA': 'NA'}
        
        _total_tc = len(test_cases)
        _progress_start = 15
        _progress_range = 15
        _next_progress = _progress_start + 5
        for _tc_idx, tc in enumerate(test_cases):
            case_data.append([
                Paragraph(_safe_text(tc.get('case_number', '')), case_cell_style),
                Paragraph(_safe_text(tc.get('module', '')), case_cell_style),
                Paragraph(_safe_text(tc.get('name', '')), case_cell_style),
                Paragraph(_safe_text(_truncate_text(tc.get('precondition', '').replace('\n', '<br/>'), 300)), case_cell_style),
                Paragraph(_safe_text(_truncate_text(tc.get('steps', '').replace('\n', '<br/>'), 300)), case_cell_style),
                Paragraph(_safe_text(_truncate_text(tc.get('expected_result', '').replace('\n', '<br/>'), 300)), case_cell_style),
                Paragraph(_safe_text(tc.get('level', '')), case_cell_center),
                Paragraph(result_map.get(tc.get('result', ''), tc.get('result', '')), case_cell_center),
                Paragraph(_safe_text(_truncate_text(tc.get('remark', ''), 300)), case_cell_style),
            ])
            if progress_callback and _total_tc > 0:
                _pct = _progress_start + int((_tc_idx + 1) / _total_tc * _progress_range)
                if _pct >= _next_progress:
                    _next_progress = _pct + 5
                    progress_callback(_pct, f'正在生成PDF内容 ({_tc_idx + 1}/{_total_tc})')
        
        case_table = Table(case_data, colWidths=[1.8*cm, 1.5*cm, 2.5*cm, 1.8*cm, 3.5*cm, 2.5*cm, 1.5*cm, 1.5*cm, 3*cm])
        
        case_style = [
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, black_border_color),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('BACKGROUND', (0, 0), (-1, 0), gray_bg),
        ]
        case_table.setStyle(TableStyle(case_style))
        elements.append(case_table)
    
    # ==================== MpList（放在用例表格后面、Issue列表前面） ====================
    mplist_headers = mplist_data.get('headers', []) if isinstance(mplist_data, dict) else []
    mplist_rows = mplist_data.get('rows', []) if isinstance(mplist_data, dict) else []
    if mplist_headers and mplist_rows:
        elements.append(Spacer(1, 8*mm))
        
        # MpList标题
        mplist_section_title_style = ParagraphStyle(
            'MpListSectionTitleStyle2', parent=styles['Normal'],
            fontName=font_name, fontSize=12, textColor=colors.black,
            alignment=TA_CENTER
        )
        mplist_section_data = [[Paragraph("<b>Mp List</b>", mplist_section_title_style)]]
        mplist_section_table = Table(mplist_section_data, colWidths=[19.6*cm])
        mplist_section_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), light_gray_bg),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(mplist_section_table)
        
        # MpList表格 - 动态列
        mp_cell_style = ParagraphStyle(
            'MpCellStyle2', parent=styles['Normal'],
            fontName=font_name, fontSize=7, textColor=colors.black,
            alignment=TA_CENTER
        )
        mp_cell_left = ParagraphStyle(
            'MpCellLeft2', parent=styles['Normal'],
            fontName=font_name, fontSize=7, textColor=colors.black,
            alignment=TA_LEFT
        )
        
        # 动态计算列宽（总宽19cm）
        num_cols = len(mplist_headers)
        if num_cols > 0:
            col_width = 19.6 / num_cols
            mp_col_widths = [col_width * cm for _ in range(num_cols)]
        else:
            mp_col_widths = []
        
        mp_header_row = [Paragraph(f"<b>{_safe_text(h)}</b>", mp_cell_style) for h in mplist_headers]
        mp_data = [mp_header_row]
        
        for row in mplist_rows:
            mp_row = []
            for i, val in enumerate(row):
                if i >= num_cols:
                    break
                mp_row.append(Paragraph(_safe_text(str(val)) if val else '-', mp_cell_left))
            mp_data.append(mp_row)
        
        mp_table = Table(mp_data, colWidths=mp_col_widths)
        mp_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, black_border_color),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('BACKGROUND', (0, 0), (-1, 0), gray_bg),
        ]))
        elements.append(mp_table)
    
    # ==================== Issue列表（放在用例表格后面，按模板 selected_fields 控制） ====================
    if is_field_visible(selected_fields, 'issue_list') and issue_list:
        elements.append(Spacer(1, 8*mm))
        
        # Issue List标题
        issue_section_title_style2 = ParagraphStyle(
            'IssueSectionTitleStyle2', parent=styles['Normal'],
            fontName=font_name, fontSize=12, textColor=colors.black,
            alignment=TA_CENTER
        )
        issue_section_data2 = [[Paragraph("<b>Issue List</b>", issue_section_title_style2)]]
        issue_section_table2 = Table(issue_section_data2, colWidths=[19.6*cm])
        issue_section_table2.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), light_gray_bg),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(issue_section_table2)
        elements.append(issue_table)
    
    # 生成PDF到内存流
    if progress_callback: progress_callback(35, '正在渲染PDF布局，请耐心等待...')
    doc.build(elements)
    if progress_callback: progress_callback(80, 'PDF渲染完成')
    stream.seek(0)
    logger.info(f"[PDF生成] PDF生成成功")
    return stream
