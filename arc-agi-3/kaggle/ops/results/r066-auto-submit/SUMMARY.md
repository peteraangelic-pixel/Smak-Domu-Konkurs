# r066 · auto-submit

STATUS=OK (UTC 2026-10-24 18:30:35)

## status[0] rc=0 petersharps/arc3-duck-original has status "KernelWorkerStatus.ERROR"

UWAGA fallback_submit: save-run nie COMPLETE, ale wersja pchnieta — submituje mimo to (Kaggle rerunuje wersje niezaleznie od naszego save-runu)

== submit ==
## competitions submit ['competitions', 'submit', '-c', 'arc-prize-2026-arc-agi-3', '-k', 'petersharps/arc3-duck-original', '-v', '8', '-f', 'arc-agi-3/kaggle/results/submission.parquet', '-m', 'arc3-duck-original v8 (=v5 config, dowod COMPLETE): Tufa Labs duck harness (June 30 milestone winner, public MIT) rerun by petersharps; attribution: Tufa Labs / jeroencottaar']
rc=1

[stderr]
400 Client Error: Bad Request for url: https://api.kaggle.com/v1/competitions.CompetitionApiService/CreateCodeSubmission


## submissions po submit (rc=0)
     ref  fileName            date                        description                                                                            status                     publicScore  privateScore  
--------  ------------------  --------------------------  -------------------------------------------------------------------------------------  -------------------------  -----------  ------------  
57247568  submission.parquet  2026-10-16 00:02:30.717000  duck v3 (smoke 29.02, kalibracja smoke->LB; slot 16.10)                                SubmissionStatus.COMPLETE  26.25                      
57201063  submission.parquet  2026-10-15 01:15:19.820000  v5-world-model-stuck (level notes + stuck audit + executable world model) git 82f2033  SubmissionStatus.COMPLETE  23.94                      
57125322  submission.parquet  2026-10-13 01:00:59.017000  v2-think-less (Franzen M2 + experiment hint + level notes + stuck audit) git 0f1f212   SubmissionStatus.COMPLETE  24.66                      
57104951  submission.parquet  2026-10-12 10:55:29.233000  t4-v2 qwen2.5-7b-nf4-bnb 5edcf932fae924ce6a1d091751b53d56c1c16ed5                      SubmissionStatus.ERROR                                
57102988  submission.parquet  2026-10-12 09:35:14.370000  t4-v2 qwen2.5-7b-nf4-bnb 4f2a7af8928240c1ec36404d55ea1ccc97654fd4                      SubmissionStatus.ERROR                                
57075036  submission.parquet  2026-10-11 13:15:18.633000  novelty-explorer baseline 9012b4f531459100e4158d1ca08d6d9523514750                     SubmissionStatus.COMPLETE  0.01                       


