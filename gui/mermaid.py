from nicegui import ui
import mermaid

# Graph of PV Cell Types (from handbook)
ui.mermaid('''
graph LR;
    id1[PV CELL TYPES]-->id2[Crystalline Silicon];
    id1[PV CELL TYPES]-->id3[Thin Film];
    id2[Crystalline Silicon]-->Polycrystalline;
    id2[Crystalline Silicon]-->Monocrystalline;
    id3[Thin Film]-->id4[Amorphous Silicon, a-Si];
    id3[Thin Film]-->id5[Tandem a-Si];
    id3[Thin Film]-->id6[Microcrystalline];
    id3[Thin Film]-->CIGS;
    id3[Thin Film]-->CdTe;
''')

# Graph of Licensing Guidelines (from handbook)
ui.mermaid('''
graph TD;
    id1[Proposed PV system]-->id2[Capacity less than 1 MW];
    id1[Proposed PV system]-->id3[Capacity 1-10 MW];
    id1[Proposed PV System]-->id4[Capacity greater than 10 MW];
    
    id4[Capacity greater than 10 MW]-->id5[Generation License];
    
    id3[Capacity 1-10 MW]-->id8[NOT Connected to Grid];
    id8[NOT Connected to Grid]-->id9[No License Required];
    
    id3[Capacity 1-10 MW]-->id6[Connected to Grid];
    id6[Connected to Grid]-->id7[Wholesaler Generation License];
    
    id2[Capacity less than 1 MW]-->id9[No License Required];
''')

# Graph of Schemes Available for Consumers (from EMA website)
ui.mermaid('''
graph TD;
    id1[Contestable Consumer]-->id2[Capacity less than 1 MWac];
    id1[Contestable Consumer]-->id3[Capacity 1-10 MWac];
    id1[Contestable Consumer]-->id4[Capacity greater than 10 MWac];
    
    id2[Capacity less than 1 MWac]-->id5[NO Payment for Excess Generation];
    id2[Capacity less than 1 MWac]-->id6[Payment for Excess Generation];
    
    id5[NO Payment for Excess Generation]-->id7[No Scheme Needed];
    id6[Payment for Excess Generation]-->id8[Enhanced Central Intermediary Scheme];
    
    id3[Capacity 1-10 MWac]-->id8[Enhanced Central Intermediary Scheme];
    id3[Capacity 1-10 MWac]-->id9[Register as MP with Energy Market Company];
    
    id4[Capacity greater than 10 MWac]-->id9[Register as MP with Energy Market Company]
    
    id10[Not Contestable Consumer]-->id11[Capacity less than 1 MWac];
    id11[Capacity less than 1 MWac]-->id12[Simplified Credit Treatment Scheme, SCT];
''')

# Graph of Installation Guide (from handbook)
ui.mermaid('''
graph TD;
    id((START))-->id1[Check with URA or qualified person, QP, if PV can be installed];
    id1[Check with URA or qualified person if PV can be installed]-->id2{Planning Required?};
    id2[Planning Required?]-->NO;
    id2[Planning Required?]-->YES;
    YES-->id3[Submit development application to URA through QP, allow 4 weeks];
    NO-->id4[Appoint PV System Contractor to assess building structure, condition, loading];
    id3[Submit development application to URA with qualified person, allow 4 weeks]-->id4[Appoint PV System Contractor to assess building structure, condition, loading];
    id4[Appoint PV System Contractor to assess building structure, condition, loading]-->id5{Compliant with loading requirements?};
    id5[Compliant with loading requirements?]-->id6[YES];
    id5[Compliant with loading requirements?]-->id7[NO];
    id6[YES]-->id8[Connecting to Grid?];
    id8[Connecting to Grid?]-->id9[NO];
    id9[NO]-->id10((END));
    id7[NO]-->id11[Submit building plans to BCA for structural strengthening, allow 14 days];
    id11[Submit building plans to BCA for structural strengthening, allow 14 days]-->id8[Connecting to Grid?];
    id8[Connecting to Grid?]-->id12[YES];
    id12[YES]-->id13[Contractor appoints Licensed Electrical Worker to install and connect PV system to grid];
    id13[Contractor appoints Licensed Electrical Worker, LEW, to install and connect PV system to grid]-->id14[LEW submits application form to SP Services];
    id14[LEW submits application form to SP Services]-->id15[SP PowerGrid evaluates technical specifications];
    id15[SP PowerGrid evaluates technical specifications]-->id16[Comply with technical requirements?];
    id16[Comply with technical requirements?]-->id17[NO];
    id17[NO]-->id15[SP PowerGrid evaluates technical specifications];
    id16[Compliant with technical requirements?]-->id18[YES];
    id18[YES]-->id19[SP PowerGrid to advise connection scheme];
    id19[SP PowerGrid to advise connection scheme]-->id20[LEW install, test, commission PV system and connection];
    id20[LEW install, test, commission PV system and connection]-->id21[inform SP Services and PowerGrid when completed];
    id21[inform SP Services and PowerGrid when completed]-->id22[Contractor O&M manual to homeowner with 12 month warranty];
    id22[Contractor O&M manual to homeowner with 12 month warranty]-->id23((END));
''')

ui.run()
