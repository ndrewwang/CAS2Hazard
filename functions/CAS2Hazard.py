def run(csv_file,export_dir):
    '''
    csv_file: csv with "name","cas","url" for the sigma aldrich product site
    export_dir: folder to save dataframe exports
    '''
    #==============================================================================
    # Libraries
    #==============================================================================
    import re
    import os
    import sys
    import time
    import pandas
    from bs4 import BeautifulSoup
    from selenium import webdriver
    import ghs_hazard_pictogram
    import requests
    header = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'} 
    #==============================================================================
    # Functions
    #==============================================================================
    def deblank(text):
        # Remove leading and trailing empty spaces
        return text.rstrip().lstrip()

    def fixencoding(text):
        # Make string compatible with cp437 characters set (Windows console)
        return text.encode(encoding="cp437", errors="ignore").decode(encoding="utf-8", errors="ignore")

    def deblankandcap(text):
        # Remove leading and trailing empty spaces, capitalize
        return text.rstrip().lstrip().capitalize()

    def striphtml(text):
        # remove HTML tags from string (from: http://stackoverflow.com/a/3398894, John Howard)
        p = re.compile(r'<.*?>')
        return p.sub('', text)

    def clean(text):
        # Deblank, fix encoding and strip HTML tags at once
        return striphtml(fixencoding(deblank(text)))




    #%%
    #==============================================================================
    # Search patterns
    #==============================================================================
    Ppattern = '(P[0-9]{3}[0-9P\+]*)' # the letter P followed by 3 digits, including '+' combo
    soloPpattern = '(P[0-9]{3})'
    #Hpattern = 'H[0-9]{3}' # the letter H followed by 3 digits
    Hpattern = '(H[0-9]{3}(?i)[ifd0-9H\+]*)' # the letter H followed by 3 digits, including '+' combo, case insensitive fd
    soloHpattern = '(H[0-9]{3}(?i)[ifd]*)'
    GHSpattern = '(GHS[0-9]{2})'


    # Parse H2P text file
    # alternate syntax : with open('') as file:
    textfile = open('HazardInfo/H2P.txt', 'r')

    # Initialize dictionary
    H2P = dict()

    for line in textfile:
        line = line.replace('\n','').replace('+ ','+') #.replace(',','')
        if re.match(Hpattern, line):
            hcode = re.match(Hpattern, line).group()
            H2P[hcode] = set(re.findall(Ppattern, line))

    # Close textfile
    textfile.close()

    # Parse P-statements text file
    textfile = open('HazardInfo/P-statements.txt', 'r')

    # Initialize dictionary
    Pstatements = dict()

    for line in textfile:
        line = line.replace('\n','').replace(' + ','+')
        if re.match(Ppattern, line):
            pcode = deblank(re.match(Ppattern, line).group())
            Pstatements[pcode] = deblank(line.split(pcode)[-1])

    # Close textfile
    textfile.close()

    # Parse H-statements text file
    textfile = open('HazardInfo/H-statements.txt', 'r')

    # Initialize dictionary
    Hstatements = dict()

    for line in textfile:
        line = line.replace('\n','').replace(' + ','+')
        if re.match(Hpattern, line):
            hcode = deblank(re.match(Hpattern, line).group())
            Hstatements[hcode] = deblank(line.split(hcode)[-1])

    # Close textfile
    textfile.close()




    #==============================================================================
    # Prevention, Response, Storage and Disposal P-statement from H-code
    #==============================================================================
    H2Prevention = dict()
    H2Response = dict()
    H2Storage = dict()
    H2Disposal = dict()

    for hcode in H2P:
        alist = H2Prevention.get(hcode,[])
        for pcode in H2P[hcode]:
            statement = Pstatements[pcode]
            if (pcode[1]=='2'): H2Prevention[hcode] = H2Prevention.get(hcode,[]); H2Prevention[hcode].append(statement)
            if (pcode[1]=='3'): H2Response[hcode]   = H2Response.get(hcode,[]); H2Response[hcode].append(statement)
            if (pcode[1]=='4'): H2Storage[hcode]    = H2Storage.get(hcode,[]); H2Storage[hcode].append(statement)
            if (pcode[1]=='5'): H2Disposal[hcode]   = H2Disposal.get(hcode,[]); H2Disposal[hcode].append(statement)
    
    #==============================================================================
    # Make Chemicals Dictionary with Safety Codes
    #==============================================================================
        
        
    # CSV with chemicals
    df = pandas.read_csv(csv_file)

    # Initialize
    chemicals=list()
    CASdict = dict()

    for index, row in df.iterrows():
        chemical = dict()
        #******************************
        Name = row['name']
        CAS = row['cas']
        sigmaURL = row['url']
        ProductNumber = sigmaURL.split('/')[-1] #Sigma Product Number
        sdspdf_url = 'https://www.sigmaaldrich.com/GB/en/sds/sial/' + ProductNumber #SDS URL
        #******************************
        chemical['CAS'] = CAS
        chemical['Name'] = Name
        chemical['ProductNumber'] = ProductNumber

        #Get website
        webpage = requests.get(sigmaURL,headers=header)
        soup = BeautifulSoup(webpage.content, "html.parser") 
        multigrid_info = soup.find_all("div",class_="MuiGrid-root MuiGrid-item MuiGrid-grid-xs-12 MuiGrid-grid-sm-3") #INSPECT ELEMENT OF "SAFETY INFORMATION" TO UPDATE

        #Get key safety info
        for i,item in enumerate(multigrid_info):

            item_str = str(item)

            # List of H-statements
            if "Hazard Statements" in item_str:
                codes = re.findall(Hpattern,item_str)
                statements = [Hstatements[code] for code in codes]
                Hazards = dict(zip(codes, statements))
                chemical['Hazards'] =  Hazards

            # List of P-statements
            if "Precautionary Statements" in item_str:
                codes = re.findall(Ppattern, item_str)
                statements = [' '.join([Pstatements[solo] for solo in re.findall(soloPpattern,code)]) for code in codes]
                Precautions = dict(zip(codes, statements))
                chemical['Precautions'] =  Precautions

            # List of supplemental (non-GHS) H-statements
            # if "Supplementary Hazards" in item_str:
            # print(item_str)

            # List of PPE
            if "Personal Protective Equipment" in item_str:
                PPE = []
                for ppe in list(item.find('p').children):
                    if '</a>' in str(ppe):
                        ppe_str = list(re.findall("(?<=>)(.*?)(?=(</a>))",str(ppe))[0])[0]
                        PPE.append(ppe_str)
                    elif len(str(ppe)) > 1:
                        ppe_str = str(ppe)
                        PPE.append(ppe_str)
                chemical['PPE'] = PPE

            # List of Pictograms
            if "Pictograms" in item_str:
                codes = re.findall(GHSpattern,item_str)
                statements = [ghs_hazard_pictogram.Hazard(code).name for code in codes]
                Pictograms = dict(zip(codes, statements))
                chemical['Pictograms'] =  Pictograms

        # Store chemical
        chemicals.append(chemical)
    # Display
    print('Processed %d chemicals out of %d CAS numbers received' % (len(chemicals),len(df)))
    
    #%% Post processing
    #==============================================================================
    # Compilation of Statements
    #==============================================================================
    # Inventory of H-, P- and PPE statements
    Hlist = list()
    HfromCAS = dict()
    HfromChemical = dict()

    Plist = list()
    PfromCAS = dict()
    PfromChemical = dict()

    PPElist=list()
    PPEfromCAS = dict()
    PPEfromChemical = dict()

    Hsupplist = list()
    HsuppfromCAS = dict()
    HsuppfromChemical = dict()

    for chemical in chemicals:
        if 'Hazards' in chemical.keys():
            for hazard in chemical['Hazards']:
                Hlist.append(hazard)
                alist = HfromCAS.get(hazard,[])
                alist.append(chemical['CAS'])
                alist = [item for item in set(alist)]
                alist.sort()
                HfromCAS[hazard] = alist

                alist = HfromChemical.get(hazard,[])
                alist.append(chemical['Name'])
                alist = [item for item in set(alist)]
                alist.sort()
                HfromChemical[hazard] = alist

        if 'Precautions' in chemical.keys():
            for precaution in chemical['Precautions']:
                Plist.append(precaution)
                alist = PfromCAS.get(precaution,[])
                alist.append(chemical['CAS'])
                alist = [item for item in set(alist)]
                alist.sort()
                PfromCAS[precaution] = alist

                alist = PfromChemical.get(precaution,[])
                alist.append(chemical['Name'])
                alist = [item for item in set(alist)]
                alist.sort()
                PfromChemical[precaution] = alist

        if 'PPE' in chemical.keys():
            for ppe in chemical['PPE']:
                PPElist.append(ppe)
                alist = PPEfromCAS.get(ppe,[])
                alist.append(chemical['CAS'])
                alist = [item for item in set(alist)]
                alist.sort()
                PPEfromCAS[ppe] = alist

                alist = PPEfromChemical.get(ppe,[])
                alist.append(chemical['Name'])
                alist = [item for item in set(alist)]
                alist.sort()
                PPEfromChemical[ppe] = alist

        if 'Supp. Hazards' in chemical.keys():
            for hazard in chemical['Supp. Hazards']:
                Hsupplist.append(hazard)
                alist = HsuppfromCAS.get(hazard,[])
                alist.append(chemical['CAS'])
                alist = [item for item in set(alist)]
                alist.sort()
                HsuppfromCAS[hazard] = alist

                alist = HsuppfromChemical.get(hazard,[])
                alist.append(chemical['Name'])
                alist = [item for item in set(alist)]
                alist.sort()
                HsuppfromChemical[hazard] = alist

    # Count instances of each H-statement
    Hdict = dict()
    for Hstatement in Hlist:
        key = Hstatement
        Hdict[key] = Hdict.get(key, 0) + 1

    # Count instances of each P-statement
    Pdict = dict()
    for Pstatement in Plist:
        key = Pstatement
        Pdict[key] = Pdict.get(key, 0) + 1

    # Count instances of each PPE recommendation
    PPEdict = dict()
    for ppe in PPElist:
        key=ppe
        PPEdict[key] = PPEdict.get(key, 0) + 1

    # Count instances of each supplemental Hazard statement
    Hsuppdict = dict()
    for statement in Hsupplist:
        key = statement
        Hsuppdict[key] = Hsuppdict.get(key, 0) + 1

    # Create a dataframe with a list of unique H-statements
    H = pandas.DataFrame(Hlist, columns = {'Code'})
    Hunique = H[H.Code!=''].drop_duplicates()

    Hunique['Count']            = Hunique['Code'].map(Hdict)
    Hunique['Statement']        = Hunique['Code'].map(Hstatements)
    Hunique['Assoc.Pcode']      = Hunique['Code'].str.slice(0,4).map(H2P)
    Hunique['Assoc.CAS']        = Hunique['Code'].map(HfromCAS)
    Hunique['Assoc.Chemical']   = Hunique['Code'].map(HfromChemical)
    Hunique['Prevention']       = Hunique['Code'].str.slice(0,4).map(H2Prevention)
    Hunique['Response']         = Hunique['Code'].str.slice(0,4).map(H2Response)
    Hunique['Storage']          = Hunique['Code'].str.slice(0,4).map(H2Storage)
    Hunique['Disposal']         = Hunique['Code'].str.slice(0,4).map(H2Disposal)

    # Create a dataframe with a list of unique P-statements
    P = pandas.DataFrame(Plist, columns = {'Code'})
    Punique = P[P.Code!=''].drop_duplicates()

    codes = Punique['Code']
    for code in codes:
        statements = [' '.join([Pstatements[solo] for solo in re.findall(soloPpattern,code)]) for code in Punique['Code']]
    Precautions = dict(zip(codes, statements))

    Punique['Count']            = Punique['Code'].map(Pdict)
    Punique['Statement']        = Punique['Code'].map(Precautions)
    Punique['Assoc.CAS']        = Punique['Code'].map(PfromCAS)
    Punique['Assoc.Chemical']   = Punique['Code'].map(PfromChemical)

    # Create a dataframe with a list of unique PPE requirements
    PPE = pandas.DataFrame(PPElist, columns = {'Item'})
    PPEunique = PPE[PPE.Item!=''].drop_duplicates()

    PPEunique['Count']            = PPEunique['Item'].map(PPEdict)
    PPEunique['Assoc.CAS']        = PPEunique['Item'].map(PPEfromCAS)
    PPEunique['Assoc.Chemical']   = PPEunique['Item'].map(PPEfromChemical)

    # # Create a dataframe with a list of unique supplemental hazards
    # Hsupp = pandas.DataFrame(Hsupplist, columns = {'Statement'})
    # Hsuppunique = Hsupp[Hsupp.Statement!=''].drop_duplicates()

    # codes = list()
    # statements = Hsuppunique['Statement']
    # for idx, statement in enumerate(statements):
    #     codes.append('Supp. %d' % (idx+1))
    # Hsuppcodes = dict(zip(statements, codes))

    # Hsuppunique['Code']            = Hsuppunique['Statement'].map(Hsuppcodes)
    # Hsuppunique['Count']            = Hsuppunique['Statement'].map(Hsuppdict)
    # Hsuppunique['Assoc.CAS']        = Hsuppunique['Statement'].map(HsuppfromCAS)
    # Hsuppunique['Assoc.Chemical']   = Hsuppunique['Statement'].map(HsuppfromChemical)

    # # Concatenate GHS Hazards and supplemental Hazards
    # Hcombo = pandas.concat([Hunique, Hsuppunique])

    
    #==============================================================================
    # Table of all chemicals
    #==============================================================================
    chemicalsDF = pandas.DataFrame(chemicals)
#     chemicalsDF['Product Number'] = chemicalsDF.apply(lambda row: '<a href="' + row['ProductURL'] + '">' + row['ProductNumber'] + '</a>',axis=1)
#     chemicalsDF['SDS'] = chemicalsDF.apply(lambda row: '<a href="' + row['SDSfile'] + '">SDS</a>',axis=1)

    #==============================================================================
    # EXPORTING CSV's
    #==============================================================================
        
    chemicalsDF.to_csv(export_dir + 'Full_Hazard_Assessment.csv',index=False)
    Hunique.to_csv(export_dir + 'Hazards.csv',index=False)
    Punique.to_csv(export_dir + 'Precautions.csv',index=False)
    PPEunique.to_csv(export_dir + 'PPE.csv',index=False)
    
    return