# r033 · recon-bundle

STATUS=OK (UTC 2026-10-16 16:26:01)

## datasets files jeroencottaar/taaf-kaggle-source-share
rc=0
Next Page Token = CfDJ8JDwKpgsc5hJpcljKjpYpOFBREkvesUmj3vDrh_ijBcdajYl-nnBe0dGNEwnJbRncwq_GrOUE8VUjNHiDG2yN9VENARj1elD03GzXp3R_R6NmsLu9rR3O0-xYXrFsU7DYj2JwxETM2zpDfnnvoIkasbOmjkqVgZvPdd0um1DxMokE1EXDs47YPdbpDI
name                                                        size  creationDate                
---------------------------------------------------------  -----  --------------------------  
README.dataset.md                                            211  2026-06-12 07:57:15.507000  
benchmark_initial.pkl                                       3281  2026-06-12 07:57:15.504000  
deploy_target.pkl                                            823  2026-06-12 07:57:15.504000  
git_status.txt                                               356  2026-06-12 07:57:15.501000  
preamble.txt                                                 976  2026-06-12 07:57:15.519000  
setup_commands.json                                        10359  2026-06-12 07:57:15.519000  
src/ARC3-Inference/Makefile                                26654  2026-06-12 07:57:15.755000  
src/ARC3-Inference/README.md                               12709  2026-06-12 07:57:15.761000  
src/ARC3-Inference/configs/eval.json                          39  2026-06-12 07:57:15.784000  
src/ARC3-Inference/configs/inference.json                   1901  2026-06-12 07:57:15.797000  
src/ARC3-Inference/configs/inference.openrouter.json        1818  2026-06-12 07:57:15.794000  
src/ARC3-Inference/configs/significance.json                 316  2026-06-12 07:57:15.783000  
src/ARC3-Inference/inference/__init__.py                      90  2026-06-12 07:57:15.814000  
src/ARC3-Inference/inference/agent/__init__.py               216  2026-06-12 07:57:15.954000  
src/ARC3-Inference/inference/agent/action_names.py          1045  2026-06-12 07:57:15.874000  
src/ARC3-Inference/inference/agent/prompts.py              13574  2026-06-12 07:57:15.852000  
src/ARC3-Inference/inference/agent/python_tool_sandbox.py  18723  2026-06-12 07:57:15.868000  
src/ARC3-Inference/inference/agent/runtime_state.py         3656  2026-06-12 07:57:16.025000  
src/ARC3-Inference/inference/agent/tool_agent.py           89299  2026-06-12 07:57:15.895000  
src/ARC3-Inference/inference/agent/vision_context.py        2311  2026-06-12 07:57:15.855000  


## datasets download jeroencottaar/taaf-kaggle-source-share
rc=0
Dataset URL: https://www.kaggle.com/datasets/jeroencottaar/taaf-kaggle-source-share
License(s): MIT
Downloading taaf-kaggle-source-share.zip to /home/runner/work/Smak-Domu-Konkurs/Smak-Domu-Konkurs/arc-agi-3/kaggle/ops/results/r033-recon-bundle/bundle


[stderr]

  0%|          | 0.00/439k [00:00<?, ?B/s]
100%|██████████| 439k/439k [00:00<00:00, 9.20MB/s]


## manifest bundle
       211  README.dataset.md
      3281  benchmark_initial.pkl
       823  deploy_target.pkl
       356  git_status.txt
       976  preamble.txt
     10359  setup_commands.json
     26654  src/ARC3-Inference/Makefile
     12709  src/ARC3-Inference/README.md
        39  src/ARC3-Inference/configs/eval.json
      1901  src/ARC3-Inference/configs/inference.json
      1818  src/ARC3-Inference/configs/inference.openrouter.json
       316  src/ARC3-Inference/configs/significance.json
        90  src/ARC3-Inference/inference/__init__.py
       216  src/ARC3-Inference/inference/agent/__init__.py
      1045  src/ARC3-Inference/inference/agent/action_names.py
     13574  src/ARC3-Inference/inference/agent/prompts.py
     18723  src/ARC3-Inference/inference/agent/python_tool_sandbox.py
      3656  src/ARC3-Inference/inference/agent/runtime_state.py
     89299  src/ARC3-Inference/inference/agent/tool_agent.py
      2311  src/ARC3-Inference/inference/agent/vision_context.py
        56  src/ARC3-Inference/inference/framework/__init__.py
     17688  src/ARC3-Inference/inference/framework/kaggle.py
     53700  src/ARC3-Inference/inference/framework/run.py
     49315  src/ARC3-Inference/inference/framework/solver.py
        53  src/ARC3-Inference/inference/tools/__init__.py
      7135  src/ARC3-Inference/inference/tools/chat.py
      1184  src/ARC3-Inference/inference/tools/config_value.py
     28385  src/ARC3-Inference/inference/tools/eval.py
      9848  src/ARC3-Inference/inference/tools/eval_plot.py
     33491  src/ARC3-Inference/inference/tools/significance.py
     27525  src/ARC3-Inference/inference/tools/traces.py
      3889  src/ARC3-Inference/inference/tools/vllm_runtime_lora_guard.py
         0  src/ARC3-Inference/inference/utils/__init__.py
       662  src/ARC3-Inference/inference/utils/grid_utils.py
      1905  src/ARC3-Inference/inference/utils/openai_compat.py
      1187  src/ARC3-Inference/inference/utils/rearc_baselines.py
      1829  src/ARC3-Inference/inference/utils/rearc_version.py
      4769  src/ARC3-Inference/inference/utils/run_artifacts.py
      8505  src/ARC3-Inference/inference/utils/segmentation.py
      3855  src/ARC3-Inference/inference/utils/viewer_artifacts.py
      2019  src/ARC3-Inference/pyproject.toml
       562  src/ARC3-Inference/scripts/ensure_server_api_key.sh
       476  src/ARC3-Inference/scripts/server_curl.sh
    362326  src/ARC3-Inference/uv.lock
        32  src/ARC3-Inference/viewer/__init__.py
     73347  src/ARC3-Inference/viewer/data.py
     54595  src/ARC3-Inference/viewer/index.html
      8933  src/ARC3-Inference/viewer/server.py
      3759  src/tufa-arc-agi-framework/Makefile
      1741  src/tufa-arc-agi-framework/README.md
      2383  src/tufa-arc-agi-framework/pyproject.toml
      3596  src/tufa-arc-agi-framework/scripts/refresh_examples.py
      1146  src/tufa-arc-agi-framework/src/taaf/__init__.py
     21393  src/tufa-arc-agi-framework/src/taaf/benchmark.py
      9568  src/tufa-arc-agi-framework/src/taaf/competition_arcade.py
     22835  src/tufa-arc-agi-framework/src/taaf/deploy.py
      6070  src/tufa-arc-agi-framework/src/taaf/deploy_inline.py
     36121  src/tufa-arc-agi-framework/src/taaf/deploy_kaggle.py
     23285  src/tufa-arc-agi-framework/src/taaf/deploy_slurm.py
    128557  src/tufa-arc-agi-framework/src/taaf/diagnostics.py
     30002  src/tufa-arc-agi-framework/src/taaf/game.py
     14742  src/tufa-arc-agi-framework/src/taaf/game_api.py
      3673  src/tufa-arc-agi-framework/src/taaf/game_examples.py
     18698  src/tufa-arc-agi-framework/src/taaf/kaggle/taaf_kaggle_run.ipynb
     26879  src/tufa-arc-agi-framework/src/taaf/kaggle/taaf_kaggle_run_share.ipynb
     10435  src/tufa-arc-agi-framework/src/taaf/kaggle_random.py
      3337  src/tufa-arc-agi-framework/src/taaf/solver.py
     12105  src/tufa-arc-agi-framework/src/taaf/solver_examples.py
      5063  src/tufa-arc-agi-framework/src/taaf/standard_benchmarks.py
       974  src/tufa-arc-agi-framework/src/taaf/support.py
    185724  src/tufa-arc-agi-framework/uv.lock
       161  taaf-kaggle-bundle.json
      1021  teardown_commands.json
(plikow: 73)
## kernels -s tufa
rc=0
ref                                                            title                                              author              lastRunTime                 totalVotes  
-------------------------------------------------------------  -------------------------------------------------  ------------------  --------------------------  ----------  
jeroencottaar/tufa-labs-duck-harness-june-30-milestone-winner  Tufa Labs duck harness [June 30 milestone winner]  Jeroen Cottaar      2026-07-01 14:54:38.057000         377  
jcole75/mindsai-tufa-2025                                      MindsAI & Tufa 2025                                Jack Cole           2025-11-14 01:17:17.410000          47  
caoyupeng/1-21-from-great-team-tufa-labs                       [1.21]from-great team-Tufa Labs                    SpeedSci            2026-07-01 17:56:53.860000          49  
lordhansolo/built-on-tufa-labs-duck-harness-milestone-2        Built on Tufa Labs duck harness - Milestone 2      Lord Han Solo       2026-10-01 18:38:35.607000          68  
wuliao0/duck-qwen3-8-anim-base                                 Duck Qwen3.8 Anim Base                             wuliao_0            2026-09-18 02:50:14.280000         288  
chiakazirim/duck-qwen3-8-tuned                                 Duck Qwen3.8 (Tuned)                               Akagha Chimgozirim  2026-09-04 20:27:08.787000         217  
keithtyser/duck-qwen3-8-flash-next-nvfp4-mtp                   Duck Qwen3.8 Flash Next NVFP4 MTP                  chiefkeith          2026-09-01 02:36:59.830000         205  
inversion/arc3-sample-submission-stochastic-goose              ARC3 Sample Submission - Stochastic Goose          inversion           2026-03-24 21:42:44.063000         738  
dfranzen/arc-agi-3-milestone-2-solution           

## kernels -s duck-harness
rc=0
ref                                                            title                                              author              lastRunTime                 totalVotes  
-------------------------------------------------------------  -------------------------------------------------  ------------------  --------------------------  ----------  
jeroencottaar/taaf-duck-harness-kaggle                         taaf-duck-harness-kaggle                           Jeroen Cottaar      2026-06-30 21:20:59.127000         262  
jeroencottaar/tufa-labs-duck-harness-june-30-milestone-winner  Tufa Labs duck harness [June 30 milestone winner]  Jeroen Cottaar      2026-07-01 14:54:38.057000         377  
boristown/agi-duck-harness-fast-eval                           【暗黑AGI】duck-harness-fast-eval                      暗黑AGI               2026-07-22 08:11:16.680000         264  
rokaiyasomapti/taaf-duck-harness-kaggle-share-resubmission     taaf-duck-harness-kaggle-share(Resubmission)       RS                  2026-07-05 10:23:34.820000         152  
lordhansolo/built-on-tufa-labs-duck-harness-milestone-2        Built on Tufa Labs duck harness - Milestone 2      Lord Han Solo       2026-10-01 18:38:35.607000          68  
kunaldesale2408/duck-harness-fast-eval                         duck-harness-fast-eval                             Kunal Desale        2026-10-12 07:00:50.907000          28  
wuliao0/duck-qwen3-8-anim-base                                 Duck Qwen3.8 Anim Base                             wuliao_0            2026-09-18 02:50:14.280000         288  
chiakazirim/duck-qwen3-8-tuned                                 Duck Qwen3.8 (Tuned)                               Akagha Chimgozirim  2026-09-04 20:27:08.787000         217  
keithtyser/duck-qwen3-8-flash-next-nvfp4-mtp      

## datasets --user driessmit1
rc=0
ref                                           title                                     size  lastUpdated                 downloadCount  voteCount  usabilityRating  
--------------------------------------------  ---------------------------------  -----------  --------------------------  -------------  ---------  ---------------  
driessmit1/vrfai-qwen3-6-27b-fp8-hf-snapshot  vrfai Qwen3.6-27B-FP8 HF snapshot  29052907734  2026-10-05 08:13:38.423000            196          0  0.5625           
driessmit1/arc3-vllm-h100-wheelhouse-v3       ARC3 vLLM H100 wheelhouse v3        5159782040  2026-10-05 07:43:09.810000            167          0  0.5625           
driessmit1/qwen3-8-27b-fp8-hf-017b9c7a        Qwen3.8-27B-FP8 HF 017b9c7a        25346275232  2026-08-18 10:47:49.810000            703          0  0.25             


## datasets --user jeroencottaar
rc=0
ref                                     title                             size  lastUpdated                 downloadCount  voteCount  usabilityRating  
--------------------------------------  -------------------------  -----------  --------------------------  -------------  ---------  ---------------  
jeroencottaar/taaf-kaggle-source-share  TAAF Kaggle Source Bundle       449765  2026-06-12 07:57:13.747000           4163          3  0.3125           
jeroencottaar/taaf-kaggle-source        TAAF Kaggle Source Bundle      2306378  2026-06-10 13:04:21.203000           2230          3  0.3125           
jeroencottaar/my-ariel-library          My ARIEL library             408361470  2024-11-04 18:28:48.383000            417         10  0.6875           
jeroencottaar/my-ariel2025-library      My ARIEL2025 library         325697681  2025-09-28 06:19:05.830000             49          2  0.5625           
jeroencottaar/seismic-release-cache     Seismic release cache        589465521  2025-07-03 05:07:51.793000              5          1  0.3125           
jeroencottaar/my-fwi-library            My FWI library                   29624  2025-07-04 04:50:07.840000             16          1  0.5              
jeroencottaar/christmas-tree-library    Christmas tree library          146118  2026-02-07 07:13:03.607000             84          3  0.4375           
jeroencottaar/christmas-tree-solution   Christmas tree solution         607960  2026-01-31 00:24:45                    93          3  0.1764706        
jeroencottaar/my-ariel2-model           my ariel2 model            10372190317  2025-09-24 06:36:47.047000             15          1  0.0625           
jeroencottaar/my-ariel2-calibration     my ariel2 calibration        338609196  2025-09-24 06:37:39.237000              3       

## datasets -s qwen3
rc=0
ref                                                          title                                                      size  lastUpdated                 downloadCount  voteCount  usabilityRating  
-----------------------------------------------------------  -------------------------------------------------  ------------  --------------------------  -------------  ---------  ---------------  
rahim3/qwen38-tpu-env-v5e8                                   qwen38-tpu-env-v5e8                                   806005009  2026-09-02 18:14:45.840000            213         11  0.5625           
bwandowando/960k-spotify-songs-lyrics-qwen3-0-6b-embeddings  🔢 960K Spotify Songs Lyrics Qwen3-0.6B Embeddings  114819873876  2025-08-23 18:55:22.040000            734         29  0.9411765        
jaytonde/qwen3-8b-map-competition                            Qwen3-8B-MAP-Competition                            12725202430  2025-08-11 01:22:45.850000            258          4  0.25             
bwandowando/5m-genius-songs-lyrics-qwen-0-6b-embeddings      🔢 5M Genius Songs Lyrics Qwen3-0.6B Embeddings 🎹    26645063553  2025-08-22 02:01:42.290000             32          8  0.9411765        
bibanh/qwen3-0-6b-embedding-finetune-epoch2                  qwen3_0_6b_embedding_finetune_epoch2                   41387154  2025-08-15 10:45:59.173000             80          3  0.1875           
zshashz/qwen3-4b-ft-jigsaw                                   Qwen3-4B-ft-jigsaw                                   2121038873  2025-07-28 13:18:54.050000              9          2  0.5625           
an0sss/qwen3-6-27b-abliberated                               Qwen3-6-27B-abliberated                             43992505254  2026-08-03 12:39:19.083000             20          2  0.9375           
laymond/rsna-knee-

## datasets -s flash-next
rc=0
ref                                                            title                                                   size  lastUpdated                 downloadCount  voteCount  usabilityRating  
-------------------------------------------------------------  ----------------------------------------------  ------------  --------------------------  -------------  ---------  ---------------  
seenmttai/qwen38-flash-next-mmproj-q8-0                        Qwen3.8 Flash Next mmproj Q8_0                     530973557  2026-09-24 13:09:53.447000              0          4  0.4375           
keithtyser/qwen38-flash-next-vllm-nvfp4-runtime-v1             Qwen3.8 Flash Next vLLM NVFP4 runtime v1          7873230742  2026-08-30 20:20:06.003000           1874          2  0.1875           
seenmttai/qwen38-flash-next-mmproj-f16                         Qwen3.8 Flash Next mmproj F16                      694753489  2026-09-24 12:58:03.113000              0          4  0.25             
alykassem202/qwen38-flash-next-vllm-nvfp4-runtime-v1           Qwen3.8 Flash Next vLLM NVFP4 runtime v1          7873230742  2026-09-04 17:07:10.137000            105          1  0.5625           
mirzamilanfarabi/albucino-qwen3-8-flash-next-drafter           albucino-Qwen3.8-Flash-Next-drafter                        0  2026-10-09 12:49:18.187000             10          1  0.4375           
mirzamilanfarabi/intel-qwen3-8-flash-next-w4a16-autoround      Intel-Qwen3.8-Flash-Next-W4A16-AutoRound                   0  2026-10-09 12:50:23.303000             16          1  0.4375           
mirzamilanfarabi/qwen3-8-flash-next-w4a16-fp8ple-mtp-albucino  Qwen3.8-Flash-Next-W4A16-FP8PLE-MTP-Albucino               0  2026-10-09 12:37:20.130000             18          1  0.5              
dfranzen/pennyroyal-v253   

## datasets -s arc3
rc=0
ref                                             title                                                 size  lastUpdated                 downloadCount  voteCount  usabilityRating  
----------------------------------------------  ---------------------------------------------  -----------  --------------------------  -------------  ---------  ---------------  
woguoat/arc3-v13-wheels                         arc3-v13-wheels                                   18093477  2026-09-09 13:22:01.807000             82          1  0.25             
driessmit1/arc3-vllm-h100-wheelhouse-v3         ARC3 vLLM H100 wheelhouse v3                    5159782040  2026-10-05 07:43:09.810000            167          0  0.5625           
saltb0x/arc3-vllm-wheelhouse-v0271-cu129        arc3-vllm-wheelhouse-v0271-cu129                6427911935  2026-08-22 09:46:18.140000            620          1  0.375            
lordhansolo/vllm-main-e975732-arc3              ARC3 vLLM main e975732                          7934814402  2026-09-30 11:38:31.013000           1386          0  0.3125           
mirzamilanfarabi/arc3-vllm-h100-wheelhouse-v3   ARC3 vLLM H100 Wheelhouse V3                    5160312018  2026-09-20 22:42:37.323000           1099          0  0.375            
wellkilo/arc3lab-duck-v12-matched-assets        ARC3Lab Duck v12 Matched Assets                   10697118  2026-08-25 09:36:33.203000            675          1  0.3125           
ataraxian/arc3-duck-prompt-v36a                 arc3-duck-prompt-v36a                               448209  2026-08-18 06:54:39.023000             22          1  0.1875           
avinavsahoo/arc3-qwen38-runtime-wheels          ARC3 Qwen38 Runtime Wheels                      3865278294  2026-08-25 15:08:30.950000              6          1  0.3125           



