"""Package isolated policy experiments on an explicitly pinned notebook.

No Kaggle push/submit. Preserve the selected base's serving and budgets.
"""
import difflib
import json
from pathlib import Path
import subprocess
import tempfile

from materialize_duck import ROOT, materialize
from lalalia_compat import source as memory_source


def build(name, notebook=None,source_output=None):
    notebook = Path(notebook) if notebook else ROOT/'duck-v18-experiment/base-v13-7.ipynb'
    nb = json.loads(notebook.read_text(encoding='utf8'))
    with tempfile.TemporaryDirectory(prefix='duck-variant-') as temp:
        tree = Path(temp)/'base'
        source = materialize(notebook,tree)
        patches = []
        def change(relative, text):
            path=source/relative
            before=path.read_text(encoding='utf8') if path.exists() else ''
            compile(text,str(path),'exec')
            patches.append('diff --git a/ARC3-Inference/'+relative+' b/ARC3-Inference/'+relative+'\n')
            if not path.exists():patches.append('new file mode 100644\n')
            patches.extend(difflib.unified_diff(before.splitlines(True),text.splitlines(True),
                'a/ARC3-Inference/'+relative if path.exists() else '/dev/null',
                'b/ARC3-Inference/'+relative))
        agent=source/'inference/agent/tool_agent.py'
        if name in ('memory','memory-v3'):
            if name=='memory-v3':
                from memory_v3 import source as selected_memory_source
            else:selected_memory_source=memory_source
            change('inference/agent/tool_agent.py',agent.read_text(encoding='utf8')+'\n\n'+selected_memory_source()+'\n')
        elif name=='router':
            change('inference/utils/codex_observation_router.py',Path(__file__).with_name('observation_router.py').read_text(encoding='utf8'))
            change('inference/agent/tool_agent.py',agent.read_text(encoding='utf8')+
                '\n\nfrom inference.utils.codex_observation_router import install as _install_codex_router\n_install_codex_router(ToolAgent)\n')
        elif name=='probe':
            change('inference/utils/codex_inspection_feedback.py',Path(__file__).with_name('inspection_feedback.py').read_text(encoding='utf8'))
            change('inference/agent/tool_agent.py',agent.read_text(encoding='utf8')+
                '\n\nfrom inference.utils.codex_inspection_feedback import install as _install_codex_feedback\n_install_codex_feedback(ToolAgent)\n')
        elif name=='template':
            change('inference/utils/codex_template_transfer.py',Path(__file__).with_name('template_transfer.py').read_text(encoding='utf8'))
            change('inference/utils/codex_template_hook.py',Path(__file__).with_name('template_hook.py').read_text(encoding='utf8'))
            change('inference/agent/tool_agent.py',agent.read_text(encoding='utf8')+
                '\n\nfrom inference.utils.codex_template_transfer import TemplateTransfer as _TemplateTransfer\n'+
                'from inference.utils.codex_template_hook import install as _install_template_controller\n'+
                '_install_template_controller(__import__(__name__, fromlist=["ToolAgent"]),_TemplateTransfer)\n')
        else:
            raise ValueError(name)
        patch=''.join(patches)
        subprocess.run(['git','apply','--include=ARC3-Inference/*','--whitespace=nowarn','-'],
            input=patch.encode(),cwd=tree,check=True)
    insertion=next(i for i,c in enumerate(nb['cells']) if 'setup_env =' in ''.join(c['source']))
    nb['cells'].insert(insertion,{'cell_type':'code','execution_count':None,'metadata':{},'outputs':[],'source':[
        'from pathlib import Path\nPath("/kaggle/codex-'+name+'.patch").write_text('+repr(patch)+')\n'+
        'ARC3_VARIANT["patch_files"].append("/kaggle/codex-'+name+'.patch")\n'+
        'ARC3_VARIANT["name"] = "codex-'+name+'-lab"\n']})
    nb['cells'][0]['source']=['# Codex '+name+' experiment\n'+
        'Unscored candidate. Base: '+str(notebook.name)+'. One isolated mechanism; serving and budget unchanged.\n'+
        ('Memory adapted from lalalia9/vickyfym and rellik13/sirikilohit; compatibility fix preserves existing level notes.\n' if name in ('memory','memory-v3') else
         'Feedback uses actual tool outcomes. No game IDs or internal engine access.\n' if name=='probe' else
         'Symbolic color relations from visible demonstrations, prediction checks and LLM fallback. No game IDs or engine access.\n' if name=='template' else
         'Observation-only strategy router and repeated-inspection guard. No game IDs or internal engine access.\n')]
    out=ROOT/'duck-lab-candidates'/name
    out.mkdir(parents=True,exist_ok=True)
    (out/'agent.ipynb').write_text(json.dumps(nb,ensure_ascii=False),encoding='utf8')
    metadata_path=notebook.parent/'kernel-metadata.json'
    if not metadata_path.exists():metadata_path=ROOT/'duck-v18-experiment/candidate/kernel-metadata.json'
    metadata=json.loads(metadata_path.read_text(encoding='utf8'))
    metadata.pop('id_no',None)
    metadata.update(id='petersharps/arc3-codex-'+name+'-lab',title='ARC3 Codex '+name+' lab',code_file='agent.ipynb')
    (out/'kernel-metadata.json').write_text(json.dumps(metadata,indent=2),encoding='utf8')
    materialize(out/'agent.ipynb',source_output or ROOT/'analysis/duck-loop-20261031'/('packaged-'+name))
    print(out,flush=True)


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--name',choices=('memory','memory-v3','router','probe','template'))
    p.add_argument('--base-notebook',type=Path)
    p.add_argument('--source-output',type=Path)
    args=p.parse_args()
    for name in ([args.name] if args.name else ('memory','router')):build(name,args.base_notebook,args.source_output)
