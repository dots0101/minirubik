# 正式繳交紀錄（尚未提交）

Phase1截止：2026-10-08 23:59 GMT+8。Phase2截止：2026-10-18 23:59 GMT+8。

本機技術驗證通過不代表收到課程accepted。以下空白保留真實資訊，不填假網址、作者或接受紀錄。

| 項目 | 狀態／待填 |
|---|---|
| 聯絡email、正式姓名 | 本人於表單填寫；避免將個人資料放公開repo |
| GitHub handle | dots0101；profile public email待核對 |
| public minirubik fork URL | [https://github.com/dots0101/minirubik](https://github.com/dots0101/minirubik)；已核對public、parent=sysprog21/minirubik |
| upstream fork commit SHA | `231796cc48868f4ea276f652139b6bebbad0cd02`；使用者本機clone及read-only查核一致 |
| default／work branch | main；遠端預設分支及本機clone已核對 |
| submitting commit SHA | 待真正提交後記錄 |
| submitted Git tag | 建议 hw1-20261008；待實際建立且推送，不是已存在tag |
| HackMD fixed published URL | 待建立；格式https://hackmd.io/@username/permalink |
| HackMD read／write permission | Everyone／Signed-in users，待設定 |
| frozen HackMD revision URL | 待筆記發布並保存revision |
| H48 method approval | 使用者已回報老師同意；待可保存的書面位置（若有） |
| AI use／required student authorship authorization | 本包揭露AI範圍；需學生完成限制項或額外同意 |
| genuine student reflection／process record | 待本人填寫，不由agent假寫成第一人稱 |
| submission form timestamp | 未提交 |
| accepted-email subject／timestamp | 未取得 |
| action-required修正紀錄 | 未知／未收到 |
| Phase2 interview date／result | 未排定；本人參加 |

依序完成：確認本人作者／AI使用符合老师允许範圍；在public fork的main匯入封裝並做真實commit；推送tag；以teaching_en.md建立英文HackMD筆記、將相對程式／evidence連結換成fork中實際路徑、發布且保留revision；核對read/write權限；提交官方表單。

[官方表單](https://forms.gle/2ZupDEdJyJkHM8Y6A)共兩頁，其公開schema已讀取：Email、Full legal name、GitHub account name、HackMD note URL、HackMD revision URL、GitHub repository、Git tag。沒有填寫或發送任何私人資訊。

收到103b0020@gs.ncku.edu.tw寄來且subject結尾為accepted，才可標示正式完成。action required則修正並重填表單；規格要求不要回覆自動信。

本機 Publish-Package.ps1 -ForkDirectory <local-fork> 預設只preview；加 -Apply才將source/evidence/doc匯入n2_lab，不登入、不commit、不push。發布時保留AI揭露、user-supplied C來源與SHA。不要把它當學生三次revision的替代。
