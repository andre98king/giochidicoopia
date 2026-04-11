# RESUME POINT: Step 4 - Related Games Integration
# File target: scripts/build_static_pages.py
# Stato attuale: Head, Footer, Styles, Scripts già sostituiti con html_fragments.*
# PROSSIMA AZIONE: Sostituire SOLO il blocco "giochi correlati" in render_static_page (IT/EN)
# REGOLA CRITICA: HTML_RELATED_CARD contiene { } CSS → usare .replace() sequenziale, MAI .format() o f-string su quel frammento.
