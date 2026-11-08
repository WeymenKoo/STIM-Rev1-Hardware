# minimal s-expression reader/writer for kicad files
import re
class Sym(str): pass
def parse(text):
    tok = re.compile(r'"(?:[^"\\]|\\.)*"|[()]|[^\s()"]+')
    stack=[[]]
    for m in tok.finditer(text):
        t=m.group(0)
        if t=='(':
            stack.append([])
        elif t==')':
            l=stack.pop(); stack[-1].append(l)
        elif t.startswith('"'):
            stack[-1].append(t[1:-1].replace('\\"','"').replace('\\\\','\\').replace('\\n','\n'))
        else:
            stack[-1].append(Sym(t))
    return stack[0]
def dump(node, ind=0):
    if isinstance(node, list):
        if not node: return "()"
        parts=[]
        simple = all(not isinstance(x,list) for x in node)
        if simple:
            return "(" + " ".join(dump(x) for x in node) + ")"
        s="("+dump(node[0])
        i=1
        while i<len(node) and not isinstance(node[i],list):
            s+=" "+dump(node[i]); i+=1
        for x in node[i:]:
            s+="\n"+"\t"*(ind+1)+dump(x,ind+1)
        s+="\n"+"\t"*ind+")"
        return s
    if isinstance(node, Sym): return str(node)
    if isinstance(node,str):
        return '"'+node.replace('\\','\\\\').replace('"','\\"').replace('\n','\\n')+'"'
    return str(node)
def find(node, name):
    return [x for x in node if isinstance(x,list) and x and x[0]==name]
def first(node,name):
    f=find(node,name); return f[0] if f else None
