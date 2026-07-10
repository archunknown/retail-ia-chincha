import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def create_manual():
    pdf_filename = "Manual_Usuario_Retail_IA_Chincha.pdf"
    
    # Setup document
    margin = 54 # 0.75 in
    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=letter,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=margin,
        bottomMargin=margin
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles matching our theme palette (Deep Dark Blue, Neon Blue, Teal)
    primary_color = colors.HexColor("#0b0f19")
    secondary_color = colors.HexColor("#1e293b")
    accent_color = colors.HexColor("#00a8cc")
    text_color = colors.HexColor("#1f2937")
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=primary_color,
        spaceAfter=15,
        alignment=1 # Center
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#4b5563"),
        spaceAfter=30,
        alignment=1 # Center
    )
    
    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=primary_color,
        spaceBefore=15,
        spaceAfter=10,
        keepWithNext=True
    )
    
    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=accent_color,
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=text_color,
        spaceAfter=8
    )
    
    bullet_style = ParagraphStyle(
        'BulletCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=text_color,
        leftIndent=20,
        firstLineIndent=-10,
        spaceAfter=4
    )
    
    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=12,
        textColor=colors.white
    )
    
    story = []
    
    # ---------------- TITLE PAGE ----------------
    story.append(Spacer(1, 1.5 * inch))
    story.append(Paragraph("MANUAL DE USUARIO", title_style))
    story.append(Paragraph("Prototipo de Gestión de Inventario Autónomo y Seguridad Perimetral", ParagraphStyle('Sub', parent=title_style, fontSize=16, leading=20, textColor=accent_color)))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Proyecto Educativo Retail IA Chincha Alta", subtitle_style))
    
    story.append(Spacer(1, 2 * inch))
    
    # Information Box table
    info_data = [
        [Paragraph("<b>Destinado a:</b> Operadores de Tienda y Personal de Seguridad", body_style)],
        [Paragraph("<b>Objetivo:</b> Monitorear y operar el almacén automatizado sin tecnicismos", body_style)],
        [Paragraph("<b>Versión:</b> 1.0 (Estable)", body_style)],
        [Paragraph("<b>Fecha:</b> Julio de 2026", body_style)]
    ]
    t_info = Table(info_data, colWidths=[5 * inch])
    t_info.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f3f4f6")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#e5e7eb")),
        ('PADDING', (0,0), (-1,-1), 12),
        ('ALIGN', (0,0), (-1,-1), 'CENTER')
    ]))
    story.append(t_info)
    
    story.append(PageBreak())
    
    # ---------------- SECTION 1 ----------------
    story.append(Paragraph("1. Introducción al Sistema", h1_style))
    story.append(Paragraph(
        "Este prototipo representa un almacén moderno e inteligente en Chincha Alta. "
        "Su propósito es asistir a operarios humanos (no desarrolladores) en dos tareas críticas cotidianas: "
        "<b>vigilar la seguridad física</b> del almacén (detectando y conteniendo intrusos) y <b>controlar el abastecimiento</b> de mercadería en estanterías de forma automatizada.",
        body_style
    ))
    story.append(Paragraph(
        "El sistema combina un robot autónomo patrullero (el <b>Guardián</b>), cámaras de seguridad con análisis digital de imágenes en tiempo real y un <b>Copiloto Conversacional inteligente</b> con el que se puede chatear en español para pedir reportes instantáneos.",
        body_style
    ))
    
    story.append(Spacer(1, 10))
    
    # ---------------- SECTION 2 ----------------
    story.append(Paragraph("2. Mapa del Almacén (Simulador 2D)", h1_style))
    story.append(Paragraph(
        "El almacén se representa visualmente como una cuadrícula interactiva de 5 filas por 5 columnas. "
        "Dentro de este mapa, cada elemento tiene una representación de color y forma específica:",
        body_style
    ))
    
    map_elements = [
        ("Pasillos (Fondo Oscuro)", "Áreas de tránsito libre por donde se desplazan el Guardián y el Intruso."),
        ("Estante Lleno (Borde Azul)", "Estanterías que contienen productos en cantidades normales (Arroz, Leche, Aceite, etc.)."),
        ("Quiebre de Stock (Borde Rojo)", "Estanterías que se han quedado sin mercadería o tienen un stock muy bajo (menos del 20%). Requieren reposición."),
        ("Guardián (Círculo Celeste 'G')", "Un robot patrullero inteligente que protege el inventario y detiene intrusos."),
        ("Intruso (Círculo Rojo 'I')", "Un agente no autorizado que se mueve de manera evasiva para sustraer productos."),
        ("Cámaras (Círculos Amarillos/Celestes)", "Los cuatro puntos de vigilancia del almacén. La cámara activa que transmite el video se ilumina en color celeste.")
    ]
    
    for title, desc in map_elements:
        story.append(Paragraph(f"• <b>{title}</b>: {desc}", bullet_style))
        
    story.append(PageBreak())
    
    # ---------------- SECTION 3 ----------------
    story.append(Paragraph("3. Guía de los Módulos del Dashboard", h1_style))
    story.append(Paragraph(
        "La pantalla principal (Dashboard) está dividida en paneles de control y monitoreo. A continuación se explica cada uno de ellos de forma sencilla:",
        body_style
    ))
    
    story.append(Paragraph("3.1. Monitoreo de Video CCTV (Pipeline de Visión)", h2_style))
    story.append(Paragraph(
        "Muestra lo que la cámara seleccionada está visualizando. Al hacer clic en las pestañas superiores, puede inspeccionar los filtros que aplica el procesador digital de imágenes:",
        body_style
    ))
    story.append(Paragraph("• <b>YOLOv8 Detect:</b> Vista final de seguridad. La inteligencia artificial dibuja un recuadro sobre los objetos (estantes o personas) mostrando un porcentaje de confianza.", bullet_style))
    story.append(Paragraph("• <b>Original:</b> Imagen cruda capturada por la cámara.", bullet_style))
    story.append(Paragraph("• <b>Grises / Filtro Gauss / Canny Edges:</b> Etapas de filtrado visual. Canny dibuja contornos brillantes sobre fondo negro, permitiendo detectar físicamente si el estante se encuentra vacío.", bullet_style))
    
    story.append(Paragraph("3.2. Panel de Control y Suspensión Ética", h2_style))
    story.append(Paragraph(
        "Este panel permite iniciar o pausar la simulación:",
        body_style
    ))
    story.append(Paragraph("• <b>Ejecutar Paso:</b> Avanza la simulación un turno. Se calcula la posición de los agentes y se actualizan los sensores.", bullet_style))
    story.append(Paragraph("• <b>Auto-Simulación:</b> Activa la marcha continua de la simulación cada 1.5 segundos.", bullet_style))
    story.append(Paragraph("• <b>Reiniciar:</b> Restablece el stock e inventario y reposiciona a los agentes a su estado inicial.", bullet_style))
    story.append(Paragraph("• <b>Banner de Confirmación Ética:</b> Si la cámara detecta al intruso con una certeza sospechosa moderada (entre 70% y 89%), el sistema se pausa. El operador humano debe evaluar la imagen del CCTV y hacer clic en <i>'Confirmar Amenaza'</i> para activar las alarmas y habilitar el movimiento de captura del Guardián.", bullet_style))

    story.append(Paragraph("3.3. Modificación de Inventario Manual", h2_style))
    story.append(Paragraph(
        "En la parte inferior izquierda, se presentan casillas numéricas para cada producto (Arroz, Leche, etc.). "
        "Usted puede ingresar cualquier valor numérico para cambiar el stock disponible. Si el valor ingresado es menor o igual a 2, "
        "verá cómo el estante en el mapa cambia dinámicamente a color rojo indicando quiebre de stock.",
        body_style
    ))

    story.append(PageBreak())
    
    # ---------------- SECTION 4 ----------------
    story.append(Paragraph("3.4. Cerebro Lógico y Copiloto de Inteligencia Artificial", h2_style))
    story.append(Paragraph(
        "Este panel es el centro intelectual del prototipo:",
        body_style
    ))
    story.append(Paragraph("• <b>Consola Prolog:</b> Muestra la base de datos de hechos lógicos activos (como posiciones en el mapa `celda(x,y)` e inventario de estantes).", bullet_style))
    story.append(Paragraph("• <b>Indicadores de Alarma:</b> Rectángulos parpadeantes que indican si la alarma de Intrusión o de Quiebre de Stock están activadas.", bullet_style))
    story.append(Paragraph("• <b>Copiloto de Seguridad Inteligente:</b> En este chat puede hacer preguntas directas en español (por ejemplo: <i>'¿Qué estantes están vacíos?'</i> o <i>'¿Dónde está la amenaza?'</i>). El sistema analizará las bases de datos locales y le responderá inmediatamente de forma concisa y amigable.", bullet_style))

    story.append(Paragraph("3.5. Búsqueda Competitiva (Pensamiento del Guardián)", h2_style))
    story.append(Paragraph(
        "Muestra cómo el robot Guardián calcula su ruta ideal usando matemáticas de teoría de juegos (Minimax). "
        "Usted podrá observar cuántas rutas y jugadas evalúa en milisegundos en el futuro para acorralar al intruso, "
        "demostrando la eficiencia del motor de toma de decisiones.",
        body_style
    ))

    # ---------------- SECTION 5 ----------------
    story.append(Paragraph("4. Guía Paso a Paso para Navegar por la Simulación", h1_style))
    story.append(Paragraph(
        "Siga esta secuencia recomendada para experimentar todas las funcionalidades del prototipo:",
        body_style
    ))
    
    steps = [
        ("Inicializar el Sistema", "Abra la dirección <code>http://127.0.0.1:8000</code> en su navegador. El sistema iniciará en pausa ética debido a la detección del intruso con un 85% de confianza."),
        ("Evaluar la Imagen de Seguridad", "Observe la pestaña <i>'YOLOv8 Detect'</i> en el panel CCTV para ver la silueta marcada del Intruso en el almacén."),
        ("Confirmar la Alerta", "Haga clic en el botón naranja <b>'Confirmar Amenaza'</b>. Las alarmas de intrusión se activarán en rojo brillante en el panel del Copiloto."),
        ("Activar la Marcha", "Haga clic en <b>'Auto-Simulación: ON'</b>. Verá cómo el Guardián (G) persigue al Intruso (I) por los pasillos paso a paso."),
        ("Consultar al Copiloto", "En la caja de texto del chat, escriba la pregunta: <i>'¿Dónde está el intruso?'</i> y presione 'Consultar'. El Copiloto le indicará las coordenadas y el estado del robot."),
        ("Simular Quiebre de Stock", "Durante la simulación, reduzca el stock de Leche a 0 en la casilla de inventario. Verá que la alarma de quiebre de stock se activa y el estante del mapa se torna rojo."),
        ("Ver la Captura", "Cuando el Guardián alcanza la celda del Intruso, la simulación concluye con éxito informando de la captura en los logs."),
        ("Reiniciar", "Haga clic en <b>'Reiniciar'</b> para restablecer la simulación a su estado inicial seguro.")
    ]
    
    for num, (title, desc) in enumerate(steps, 1):
        story.append(Paragraph(f"<b>Paso {num} — {title}:</b> {desc}", bullet_style))

    # Build document
    doc.build(story)
    print("PDF creado exitosamente.")

if __name__ == "__main__":
    create_manual()
