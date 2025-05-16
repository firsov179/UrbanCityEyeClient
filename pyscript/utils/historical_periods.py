"""
Module containing historical period definitions and helper functions
"""

HISTORICAL_PERIODS = {
    13: {
        "name": "Late Middle Ages",
        "description": "The Late Middle Ages was characterized by social and political upheaval. Cities grew as centers of trade, while the Black Death devastated Europe's population. This period saw the rise of universities and early developments in art and architecture.",
        "name_ru": "Позднее Средневековье",
        "description_ru": "Позднее Средневековье характеризовалось социальными и политическими потрясениями. Города росли как центры торговли, в то время как Черная смерть опустошила население Европы. В этот период наблюдался рост университетов и ранние разработки в искусстве и архитектуре."
    },
    14: {
        "name": "Late Middle Ages",
        "description": "The 14th century witnessed the beginning of the Renaissance in Italy, the Hundred Years' War between England and France, and recovery from the Black Death. Urban centers continued to develop with growing merchant classes.",
        "name_ru": "Позднее Средневековье",
        "description_ru": "В XIV веке начался Ренессанс в Италии, продолжалась Столетняя война между Англией и Францией, и происходило восстановление после Черной смерти. Городские центры продолжали развиваться с растущими купеческими классами."

    },
    15: {
        "name": "Renaissance",
        "description": "The 15th century marked the height of the Renaissance in Europe, with significant advancements in art, architecture, and science. The printing press was invented, enabling the spread of knowledge, while exploration began to expand European influence worldwide.",
        "name_ru": "Эпоха Возрождения",
        "description_ru": "XV век ознаменовал расцвет Ренессанса в Европе, со значительными достижениями в искусстве, архитектуре и науке. Был изобретен печатный станок, что позволило распространять знания, а исследования начали расширять европейское влияние по всему миру."
    },
    16: {
        "name": "Age of Discovery",
        "description": "The 16th century was defined by European exploration and colonization, the Protestant Reformation, and the rise of powerful monarchies. Cities expanded with new architectural styles reflecting Renaissance ideals and emerging trade wealth.",
        "name_ru": "Эпоха открытий",
        "description_ru": "XVI век определялся европейскими исследованиями и колонизацией, Протестантской Реформацией и ростом могущественных монархий. Города расширялись с новыми архитектурными стилями, отражающими идеалы Ренессанса и растущее торговое богатство."
    },
    17: {
        "name": "Age of Enlightenment",
        "description": "The 17th century saw the Scientific Revolution, baroque architecture, and the establishment of colonial empires. European cities began planned expansions with grand boulevards and public spaces as absolutist monarchs displayed their power through urban design.",
        "name_ru": "Эпоха Просвещения",
        "description_ru": "В XVII веке произошла Научная революция, развивалась барочная архитектура и устанавливались колониальные империи. Европейские города начали плановые расширения с грандиозными бульварами и общественными пространствами, поскольку абсолютистские монархи демонстрировали свою власть через городской дизайн."

    },
    18: {
        "name": "Industrial Revolution",
        "description": "The 18th century was marked by the beginning of the Industrial Revolution, the Age of Enlightenment, and political revolutions. Cities started to transform dramatically with factories, working-class neighborhoods, and new infrastructure challenges.",
        "name_ru": "Промышленная революция",
        "description_ru": "XVIII век ознаменовался началом Промышленной революции, Эпохой Просвещения и политическими революциями. Города начали резко трансформироваться, появились фабрики, рабочие кварталы и новые инфраструктурные проблемы."

    },
    19: {
        "name": "Victorian Era",
        "description": "The 19th century witnessed rapid industrialization, extensive railroad construction, and significant urban growth. Cities expanded dramatically with industrial zones, workers' housing, and the emergence of modern urban planning to address overcrowding and sanitation.",
        "name_ru": "Викторианская эпоха",
        "description_ru": "XIX век стал свидетелем быстрой индустриализации, обширного строительства железных дорог и значительного роста городов. Города драматически расширялись с промышленными зонами, жильем для рабочих и появлением современного городского планирования для решения проблем перенаселенности и санитарии."
    },
    20: {
        "name": "Modern Era",
        "description": "The 20th century transformed cities through automobile transportation, suburban expansion, and modernist urban planning. Two World Wars and economic shifts reshaped urban landscapes, while latter decades saw urban renewal and early computerization.",
        "name_ru": "Современная эпоха",
        "description_ru": "XX век преобразил города благодаря автомобильному транспорту, пригородному расширению и модернистскому городскому планированию. Две мировые войны и экономические сдвиги изменили городские ландшафты, а в последние десятилетия началось обновление городов и ранняя компьютеризация."

    },
    21: {
        "name": "Information Age",
        "description": "The 21st century is characterized by digital technology, globalization, and growing focus on sustainability. Cities face challenges of climate change, inequality, and technological integration while developing smart infrastructure and sustainable design.",
        "name_ru": "Информационная эпоха",
        "description_ru": "XXI век характеризуется цифровыми технологиями, глобализацией и растущим вниманием к устойчивому развитию. Города сталкиваются с проблемами изменения климата, неравенства и технологической интеграции, разрабатывая умную инфраструктуру и устойчивый дизайн."
    }
}

def get_century(year):
    """
    Get the century for a given year
    
    Args:
        year: Year to get century for
        
    Returns:
        Century number (e.g. 19 for 1850)
    """
    return (year - 1) // 100 + 1

def get_historical_period(year):
    """
    Get historical period information for a given year
    
    Args:
        year: Year to get period for
        
    Returns:
        Dictionary with period information or default period if not found
    """
    century = get_century(year)
    
    return HISTORICAL_PERIODS.get(century, {
        "name": f"{century}th Century",
        "description": f"This period in the {century}th century saw significant developments in urban spaces and infrastructure, though detailed information is not available."
    })
