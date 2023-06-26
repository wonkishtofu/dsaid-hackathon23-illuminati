from nicegui import ui

ui.mermaid('''
graph LR;
    PV_CELL_TYPES-->Crystalline_Silicon;
    PV_CELL_TYPES-->Thin_Film;
    Crystalline_Silicon-->Polycrystalline;
    Crystalline_Silicon-->Monocrystalline;
    Thin_Film-->Amorphous_Si;
    Thin_Film-->Microcrystalline;
    Thin_Film-->CIGS;
    Thin_Film-->CdTe;
''')

ui.mermaid('''
graph TD;
    Capacity-->10+MW;
    Capacity-->1-10MW;
    Capacity-->1-MW;
    10+MW-->GenerationLicense;
    1-10MW-->GridConnected;
    GridConnected-->WholesalerLicense;
    1-10MW-->NoLicense;
    1-MW-->NoLicense;
''')

ui.run()
