import ast, difflib, json, pathlib, shutil, subprocess, tempfile
D = pathlib.Path(__file__).resolve().parent
nb = json.loads((D/'base-v13-7.ipynb').read_text(encoding='utf8'))
with tempfile.TemporaryDirectory() as temp:
    root = pathlib.Path(temp)
    src = 'ARC3-Inference'
    shutil.copytree(D.parent/'kaggle/ops/results/r033-recon-bundle/bundle/src'/src, root/src)
    def apply(s):
        subprocess.run(['git','apply','--include=ARC3-Inference/*','--whitespace=nowarn','-'],input=(s.rstrip('\n')+'\n').encode(),cwd=root,check=True)
    for i in range(6,16):
        s=''.join(nb['cells'][i]['source'])
        apply(s.split('\n',1)[1] if i==6 else next(x.value for x in ast.walk(ast.parse(s)) if isinstance(x,ast.Constant) and isinstance(x.value,str) and x.value.startswith(('diff --git','--- a/'))))
    changes=[]
    def change(path,old,new):
        path=src+'/inference/'+path
        s=(root/path).read_text(encoding='utf8')
        assert s.count(old)==1,(path,old)
        t=s.replace(old,new)
        changes.extend(difflib.unified_diff(s.splitlines(True),t.splitlines(True),'a/'+path,'b/'+path))
    change('utils/world_model.py','def wm_default_actions(', (D/'clicks.py').read_text(encoding='utf-8-sig')+'\n\ndef wm_default_actions(')
    anchor='            report = wm_plan(start,'
    change('agent/python_tool_sandbox.py',anchor,'            if actions is None and "MOUSE" in valid:\n                searched.extend(wm_click_actions(runtime_globals.get("current_frame"), runtime_globals.get("transitions")))\n'+anchor)
    change('agent/python_tool_sandbox.py','MOUSE clicks were not searched; pass actions=[...] to include them','Candidate clicks were inferred from visible objects and recent clicks. Pass actions to override.')
    change('agent/prompts.py','MOUSE clicks are searched only when you list them in `actions`.','For MOUSE games plan() tries observed clicks and visible object centers. Override actions for empty-space targets. Test predicted effects before committing the route.')
    patch=''.join(changes)
    apply(patch)
    for p in ('agent/python_tool_sandbox.py','agent/prompts.py','utils/world_model.py'):
        compile((root/src/'inference'/p).read_text(encoding='utf8'),p,'exec')
    cell=nb['cells'][15]
    cell['source']=[''.join(cell['source'])+'\nfrom pathlib import Path\nPath("/kaggle/duck-v18-clicks.patch").write_text('+repr(patch)+')\nARC3_VARIANT["patch_files"].append("/kaggle/duck-v18-clicks.patch")\n']
    nb['cells'][0]['source']=['# Duck v18 — visual click planner\nExperimental variant of v13.7, cap=0. Explicit action lists take precedence.']
    out=D/'candidate'; out.mkdir(exist_ok=True)
    (out/'arc3-duck-v18.ipynb').write_text(json.dumps(nb,ensure_ascii=False),encoding='utf8')
