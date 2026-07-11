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
    
    # Custom colors: Deep Indigo, Dark Slate, Vibrant Teal, Charcoal Text
    primary_color = colors.HexColor("#0f172a")
    secondary_color = colors.HexColor("#1e293b")
    accent_color = colors.HexColor("#0ea5e9")
    text_color = colors.HexColor("#334155")
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=primary_color,
        spaceAfter=12,
        alignment=1 # Center
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=25,
        alignment=1 # Center
    )
    
    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=19,
        textColor=primary_color,
        spaceBefore=12,
        spaceAfter=8,
        keepWithNext=True
    )
    
    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=accent_color,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=text_color,
        spaceAfter=8
    )
    
    bullet_style = ParagraphStyle(
        'BulletCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=text_color,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )
    
    story = []
    
    # ---------------- PORTADA ----------------
    story.append(Spacer(1, 1.5 * inch))
    story.append(Paragraph("MANUAL DE USUARIO", title_style))
    story.append(Paragraph("SISTEMA DE GESTIÓN AUTÓNOMA DE INVENTARIO Y SEGURIDAD", ParagraphStyle('Sub', parent=title_style, fontSize=14, leading=18, textColor=accent_color)))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Guía Práctica e Intuitiva para Operadores de Almacén", subtitle_style))
    
    story.append(Spacer(1, 1.8 * inch))
    
    info_data = [
        [Paragraph("<b>Proyecto:</b> Retail IA - Chincha Alta", body_style)],
        [Paragraph("<b>Propósito:</b> Control inteligente de stock y respuesta a intrusiones sin tecnicismos", body_style)],
        [Paragraph("<b>Público Objetivo:</b> Operadores de tienda, personal de logística y seguridad", body_style)],
        [Paragraph("<b>Estado de Aplicación:</b> Fase 1 (Simulación Operativa Local)", body_style)]
    ]
    t_info = Table(info_data, colWidths=[5 * inch])
    t_info.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1")),
        ('PADDING', (0,0), (-1,-1), 10),
        ('ALIGN', (0,0), (-1,-1), 'CENTER')
    ]))
    story.append(t_info)
    
    story.append(PageBreak())
    
    # ---------------- ¿QUÉ ES Y PARA QUÉ SIRVE? ----------------
    story.append(Paragraph("1. ¿Qué es este sistema y para qué sirve?", h1_style))
    story.append(Paragraph(
        "Este prototipo es una herramienta interactiva diseñada para simular y gestionar las operaciones diarias de un almacén "
        "de retail en Chincha. El sistema integra sensores virtuales, lógica automatizada y un robot patrullero para resolver "
        "dos problemas comunes en la logística de tiendas: <b>la sustracción no autorizada de mercadería</b> y el <b>desabastecimiento de productos</b> en estanterías.",
        body_style
    ))
    
    story.append(Paragraph("1.1. Usos Prácticos y Beneficios Principales", h2_style))
    story.append(Paragraph(
        "Este prototipo permite realizar múltiples tareas operativas en la práctica:",
        body_style
    ))
    story.append(Paragraph("• <b>Prevención de Pérdidas sin Vigilancia Constante:</b> El sistema detecta automáticamente la presencia de personas en zonas restringidas y despliega al robot de forma inmediata sin necesidad de que el operador supervise la pantalla todo el día.", bullet_style))
    story.append(Paragraph("• <b>Monitoreo Remoto del Nivel de Abastecimiento:</b> Avisa visualmente mediante alarmas y estanterías en color rojo cuando un producto se agota, facilitando la orden rápida de reposición.", bullet_style))
    story.append(Paragraph("• <b>Auditoría Conversacional por Voz o Texto:</b> Permite al gerente de tienda preguntar directamente <i>'¿Qué estante necesita reposición?'</i> y obtener una respuesta redactada en español natural, eliminando la necesidad de leer complicadas tablas de datos.", bullet_style))
    story.append(Paragraph("• <b>Entrenamiento de Personal:</b> Sirve como simulador interactivo para enseñar a nuevos operarios cómo responder ante alertas y coordinar tareas de seguridad en tienda.", bullet_style))

    story.append(Spacer(1, 10))

    # ---------------- EXPLICACIÓN DE LOS 6 MÓDULOS ----------------
    story.append(Paragraph("2. Descripción de los Módulos del Sistema", h1_style))
    story.append(Paragraph(
        "El panel de control (Dashboard) está dividido en 6 módulos intuitivos que interactúan entre sí. A continuación se detalla su uso:",
        body_style
    ))
    
    story.append(Paragraph("2.1. SIMULADOR DE ALMACÉN 2D", h2_style))
    story.append(Paragraph(
        "Es el mapa dinámico que muestra una vista aérea del almacén (5 filas por 5 columnas). Le permite ubicar físicamente los componentes en tiempo real:<br/>"
        "- <b>Pasillos (Fondo Gris):</b> Caminos transitables.<br/>"
        "- <b>Estantes con Borde Azul:</b> Almacenes llenos de mercadería.<br/>"
        "- <b>Estantes con Borde Rojo:</b> Productos agotados (quiebre de stock).<br/>"
        "- <b>Círculo Celeste ('G'):</b> Posición actual del robot Guardián.<br/>"
        "- <b>Círculo Rojo ('I'):</b> Posición actual del Intruso dentro del almacén.<br/>"
        "- <b>Círculos Amarillos/Celestes:</b> Ubicación de las cámaras. La cámara que transmite en vivo se ilumina de color celeste.<br/>"
        "- <b>Juego Interactivo Manual:</b> Con la Auto-Simulación apagada, usted puede cliquear directamente en las celdas adyacentes al Intruso ('I') para moverlo manualmente (por los pasillos o hacia los estantes para robarlos). El Guardián ('G') reaccionará inmediatamente calculando su movimiento de persecución mediante inteligencia artificial.",
        body_style
    ))
    
    story.append(PageBreak())

    story.append(Paragraph("2.2. PANEL DE CONTROL", h2_style))
    story.append(Paragraph(
        "Es la botonera principal para manejar el tiempo de la simulación. Cuenta con tres botones principales:<br/>"
        "- <b>Ejecutar Paso:</b> Avanza la simulación un turno (mueve a los agentes y actualiza las cámaras).<br/>"
        "- <b>Auto-Simulación:</b> Hace que el sistema corra de forma continua y automática en tiempo real.<br/>"
        "- <b>Reiniciar:</b> Restablece todo el inventario y reposiciona a los agentes al estado inicial de alerta.<br/>"
        "- <b>Caja de Suspensión Ética (Banner Naranja):</b> Cuando la cámara de IA detecta un intruso con duda moderada (certeza entre 70% y 89%), la simulación se congela. El módulo exige al operador hacer clic en <b>'Confirmar Amenaza'</b> para liberar el movimiento de persecución del robot, o <b>'Descartar Alerta'</b> si es una falsa alarma.",
        body_style
    ))

    story.append(Paragraph("2.3. MONITOREO DE CÁMARAS (PIPELINE OPENCV / YOLOv8)", h2_style))
    story.append(Paragraph(
        "Muestra el flujo de video en vivo de la cámara seleccionada en la lista desplegable. Cuenta con pestañas superiores que permiten ver cómo el procesador digital descompone la imagen para analizarla:<br/>"
        "- <b>YOLOv8 Detect:</b> Vista de IA. Dibuja recuadros de color alrededor del intruso y los estantes, estimando el porcentaje de certeza física.<br/>"
        "- <b>Original:</b> Transmisión visual sin alteraciones.<br/>"
        "- <b>Grises / Filtro Gauss / Canny Edges:</b> Filtros de contorno en blanco y negro. Sirven para rastrear físicamente la silueta de los estantes y verificar si la mercadería ha desaparecido.",
        body_style
    ))

    story.append(Paragraph("2.4. MODIFICAR INVENTARIO MANUAL", h2_style))
    story.append(Paragraph(
        "Es un panel de entrada directa de datos ubicado en la columna izquierda. Contiene casillas numéricas para ajustar el stock disponible de cada producto (Arroz, Azúcar, Leche, etc.). "
        "Permite al operador simular manualmente el desabastecimiento: si escribe un número bajo (2 o menos), el sistema disparará las alertas de reposición y cambiará el estante en el mapa 2D a color rojo.",
        body_style
    ))

    story.append(Paragraph("2.5. CEREBRO LÓGICO Y COPILOTO CONVERSACIONAL", h2_style))
    story.append(Paragraph(
        "Representa la mente del almacén. Contiene dos áreas:<br/>"
        "- <b>Hechos Prolog e Inferencia:</b> Muestra la base de datos de reglas lógicas activas y el nivel de peligro (Bajo, Medio, Crítico).<br/>"
        "- <b>Alarmas de Intrusión y Quiebre:</b> Indicadores luminosos que parpadean cuando hay una amenaza.<br/>"
        "- <b>Copiloto de Seguridad:</b> Caja de chat amigable. El operador puede escribir preguntas como <i>'¿Qué estante está vacío?'</i> o <i>'¿Qué debo hacer ahora?'</i> y el asistente local responderá de manera comprensible indicando los pasos a seguir.",
        body_style
    ))

    story.append(Paragraph("2.6. BÚSQUEDA COMPETITIVA (MINIMAX ALFA-BETA DEPTH 4)", h2_style))
    story.append(Paragraph(
        "Es el visor del cerebro táctico del robot Guardián. Muestra en lenguaje simple cómo el robot realiza cálculos matemáticos en milisegundos "
        "para proyectar y predecir los movimientos del intruso a 4 jugadas de anticipación en el futuro, permitiéndole acorralarlo eficientemente "
        "por la ruta más corta sin quedar atrapado en pasillos sin salida.",
        body_style
    ))

    story.append(PageBreak())

    # ---------------- GUÍA PASO A PASO ----------------
    story.append(Paragraph("3. Guía Paso a Paso para Operar el Sistema", h1_style))
    story.append(Paragraph(
        "Siga esta secuencia de operaciones en el navegador para explorar el funcionamiento interactivo del prototipo:",
        body_style
    ))
    
    steps = [
        ("Carga Inicial", "Acceda a la URL de la simulación. Notará que inicia en pausa y el panel muestra un banner naranja de advertencia ética por sospecha de intrusión al 85%."),
        ("Inspección de Video", "En el panel de cámaras (CCTV), observe las pestañas <i>'YOLOv8'</i> y <i>'Canny Edges'</i> para verificar la silueta detectada en el pasillo."),
        ("Autorizar al Robot", "Haga clic en el botón naranja <b>'Confirmar Amenaza'</b>. Esto activará las sirenas y alarmas luminosas en el panel del Copiloto."),
        ("Iniciar la Marcha", "Haga clic en <b>'Auto-Simulación: ON'</b>. Verá en el mapa 2D cómo el robot Guardián ('G') se desliza de forma fluida para perseguir al Intruso ('I')."),
        ("Preguntar al Copiloto", "Escriba en la caja de chat: <i>'¿cuál es el estado de las alarmas?'</i> o <i>'¿dónde está el intruso?'</i> y presione 'Consultar'. El asistente local le dará un reporte instantáneo."),
        ("Simular Desabastecimiento", "Cambie la cantidad de Leche a 0 en la casilla de inventario manual. Observe cómo se enciende la alarma de 'Quiebre de Stock' y el estante respectivo en el mapa 2D se torna rojo."),
        ("Captura y Cierre", "Observe en el mapa cómo el Guardián intercepta al Intruso. La simulación se detendrá automáticamente registrando el éxito en la bitácora."),
        ("Reinicio Seguro", "Haga clic en <b>'Reiniciar'</b> para restablecer los valores de stock y devolver a los agentes a su posición inicial segura de patrullaje.")
    ]
    
    for num, (title, desc) in enumerate(steps, 1):
        story.append(Paragraph(f"<b>Paso {num} — {title}:</b> {desc}", bullet_style))

    # Build document
    doc.build(story)
    print("PDF creado exitosamente.")

if __name__ == "__main__":
    create_manual()
