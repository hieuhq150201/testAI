# mac-security-check

Tool kiểm tra bảo mật nhanh trên macOS sau khi nghi ngờ chạy phần mềm độc hại.

## Chạy thế nào

```bash
bash check.sh
```

Hoặc output JSON:

```bash
bash check.sh --json
```

## Kiểm tra những gì

| # | Mục | Mô tả |
|---|-----|--------|
| 1 | System info | OS version, kernel |
| 2 | FileVault | Disk encryption có bật không |
| 3 | Firewall | Application Firewall + Stealth mode |
| 4 | SIP | System Integrity Protection |
| 5 | Listening ports | Port nào đang mở |
| 6 | Suspicious processes | ngrok, netcat, xmrig, reverse shell, v.v. |
| 7 | LaunchAgents/Daemons | Plist mới tạo gần đây (7 ngày) |
| 8 | Login Items | App tự chạy khi login |
| 9 | Active connections | TCP connections đang mở |
| 10 | Modified sensitive files | .ssh, .zshrc, /etc/hosts, crontab |
| 11 | Sudo access | Quyền leo thang |
| 12 | Auto-update | Software update có bật không |

## Nếu thấy bất thường

1. **Ngắt mạng** trước
2. **Backup** ngay nếu chưa có
3. **Đổi password** các tài khoản quan trọng (từ máy khác)
4. Kiểm tra kỹ các file trong `~/Library/LaunchAgents/`
5. Cân nhắc reinstall macOS nếu SIP bị tắt hoặc thấy process lạ
