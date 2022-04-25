import cirpy

def make_compound_dict(identifier,name):

    mol = dict()
#     mol['iupac'] = cirpy.resolve(identifier, 'iupac_name')
    mol['formula'] = cirpy.resolve(identifier, 'formula')
    mol['smiles'] = cirpy.resolve(identifier, 'smiles')
#     mol['inchi'] = cirpy.resolve(identifier, 'inchi')
#     mol['stdinchi'] = cirpy.resolve(identifier, 'stdinchi')
#     mol['stdinchikey'] = cirpy.resolve(identifier, 'stdinchikey')
    mol['cas'] = cirpy.resolve(identifier, 'cas')
#     mol['molecular_weight'] = cirpy.resolve(identifier, 'mw')
#     mol['name'] = cirpy.resolve(identifier, 'names')
    mol['name']=name

    return mol