"""Dependency-free evaluator for the JSON Schema vocabulary used by this package.
Not a general JSON Schema engine; unsupported validation keywords fail closed.
"""
import re
ANNOTATIONS={'$schema','$id','$defs','title','description','default','examples'}
SUPPORTED={'$ref','type','properties','required','additionalProperties','items','enum','const','minimum','minLength','pattern','minItems','uniqueItems'}
def check(value,schema,root=None,path='$'):
    root=schema if root is None else root
    unknown=set(schema)-ANNOTATIONS-SUPPORTED
    if unknown: raise ValueError('unsupported schema keywords '+repr(unknown))
    if '$ref' in schema:
        ref=schema['$ref']
        if not ref.startswith('#/'): raise ValueError('external schema ref unsupported')
        node=root
        for k in ref[2:].split('/'): node=node[k.replace('~1','/').replace('~0','~')]
        check(value,node,root,path)
    def istype(t):
        return {'object':isinstance(value,dict),'array':isinstance(value,list),'string':isinstance(value,str),'integer':isinstance(value,int) and not isinstance(value,bool),'number':isinstance(value,(int,float)) and not isinstance(value,bool),'boolean':isinstance(value,bool),'null':value is None}.get(t,False)
    types=schema.get('type')
    if types is not None and not any(istype(t) for t in (types if isinstance(types,list) else [types])): raise ValueError(path+' type')
    if 'const' in schema and value!=schema['const']: raise ValueError(path+' const')
    if 'enum' in schema and value not in schema['enum']: raise ValueError(path+' enum')
    if isinstance(value,dict):
        for k in schema.get('required',[]):
            if k not in value: raise ValueError(path+' missing '+k)
        props=schema.get('properties',{})
        for k,v in value.items():
            if k in props: check(v,props[k],root,path+'.'+k)
            elif schema.get('additionalProperties') is False: raise ValueError(path+' extra '+k)
            elif isinstance(schema.get('additionalProperties'),dict): check(v,schema['additionalProperties'],root,path+'.'+k)
    if isinstance(value,list):
        if len(value)<schema.get('minItems',0): raise ValueError(path+' minItems')
        if schema.get('uniqueItems') and any(value[i] in value[:i] for i in range(len(value))): raise ValueError(path+' uniqueItems')
        for i,v in enumerate(value):
            if 'items' in schema: check(v,schema['items'],root,path+'['+str(i)+']')
    if isinstance(value,str):
        if len(value)<schema.get('minLength',0): raise ValueError(path+' minLength')
        if 'pattern' in schema and re.search(schema['pattern'],value) is None: raise ValueError(path+' pattern')
    if isinstance(value,(int,float)) and not isinstance(value,bool) and 'minimum' in schema and value<schema['minimum']: raise ValueError(path+' minimum')
