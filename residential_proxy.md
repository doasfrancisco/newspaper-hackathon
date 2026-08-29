# The residential proxy

`get_news.md` and `reading_tweets_via_api.md` tell you to confirm the proxy exit
IP before you read the timeline. This file tells you what that proxy is and how
it works.

All real values are placeholders. Put your own values in a `.env` file that
`.gitignore` excludes.

## 1. Why a residential IP is necessary

- The X API v2 has no "For You" endpoint. It gives only the reverse
  chronological Following timeline. The ranked feed exists only in a logged-in
  browser session.
- Every IP belongs to an autonomous system (AS). Anti-bot systems read the AS
  and classify it.

| Exit | Class | How X reads it |
|---|---|---|
| Cloud VPS | `hosting` | A server. Suspicious. |
| Commercial residential proxy | `isp` | Residential, but new and shared. |
| Your home line | `isp` | Normal, and the account knows it. |

The home line is the strongest option, and it has no cost.

## 2. The chain

```
  Chromium on the VPS
        |  socks5://127.0.0.1:1080            no password
        v
  gost client on the VPS      (service "socks-in")
        |  socks5://<PHONE_TAILNET_IP>:1080   adds the username and password
        |  through the mesh VPN, encrypted
        v
  gost server on the phone
        |  binds the tailnet address only
        v
  phone wlan0  ->  home Wi-Fi  ->  home ISP
        v
  Public exit: <PROXY_EXIT_IP>
```

Chromium discards SOCKS5 credentials. Thus the local gost client adds them.
This is the reason for the two gost instances.

## 3. The parts

| Part | Function |
|---|---|
| An Android phone on the home Wi-Fi | Gives the residential exit |
| `gost` (GO Simple Tunnel) on the phone | SOCKS5 on 1080, HTTP CONNECT on 8080, with a password |
| A mesh VPN (Tailscale) on the phone and the VPS | The only route to the proxy ports |
| `adb` over the mesh VPN, port 5555 | Starts and repairs gost |
| `gost` on the VPS | Local relay that adds the credentials |
| `proxyguard.sh` + a systemd unit on the VPS | Watchdog. Restarts gost when a port closes |

`gost` starts through `adb shell`, thus Android sees a shell process, not an
app. Its `oom_score_adj` is -1000. The low-memory killer cannot select it. An
app with a foreground service gets 200 and Android kills it.

## 4. The phone configuration

`/data/local/tmp/gost.yaml`, mode 600:

```yaml
log:
  output: /data/local/tmp/gost.log
  level: warn
  format: json
resolvers:
  - name: res0
    nameservers:
      - addr: 1.1.1.1:53
      - addr: 8.8.8.8:53
      - addr: <ISP_DNS_1>:53
      - addr: <ISP_DNS_2>:53
services:
  - name: socks
    addr: "<PHONE_TAILNET_IP>:1080"
    resolver: res0
    handler:
      type: socks5
      auth:
        username: <PROXY_USERNAME>
        password: <PROXY_PASSWORD>
    listener:
      type: tcp
  - name: http
    addr: "<PHONE_TAILNET_IP>:8080"
    resolver: res0
    handler:
      type: http
      auth:
        username: <PROXY_USERNAME>
        password: <PROXY_PASSWORD>
    listener:
      type: tcp
```

gost on Android cannot resolve names without the `resolvers` block. Keep the
ISP resolvers last, because some networks block port 53 to external servers.

## 5. Ports

| Where | Port | Service | Reachable from |
|---|---|---|---|
| Phone | 1080 | gost SOCKS5, password | Mesh VPN only |
| Phone | 8080 | gost HTTP CONNECT, password | Mesh VPN only |
| Phone | 5555 | adb | Mesh VPN and LAN |
| VPS | 127.0.0.1:1080 | gost relay | The VPS only |

## 6. How to use it

Command line:

```
curl -x "socks5h://<USER>:<PASS>@<PHONE_TAILNET_IP>:1080" https://x.com
```

Use `socks5h`, with the `h`. Plain `socks5` sends the DNS queries to your local
network.

Playwright:

```python
browser = p.chromium.launch(proxy={
    "server": f"http://{PROXY_HOST}:8080",
    "username": PROXY_USERNAME,
    "password": PROXY_PASSWORD,
})
```

Firefox: use SOCKS on 1080 and tick "Proxy DNS when using SOCKS v5". Chromium
browsers must use the HTTP proxy on 8080.

The `playwright_open` MCP tool starts the Chromium that already holds the x.com
session and confirms the exit IP. It refuses if the IP is not correct.

## 7. Health check

```
systemctl is-active proxyguard.service
tail -5 ~/proxyguard.log
curl -s --socks5-hostname 127.0.0.1:1080 https://ipinfo.io/json
```

The result must show `<PROXY_EXIT_IP>` and your home ISP. If it shows the
public IP of the VPS or the cloud vendor name, the chain is broken. Stop.

Use a navigation to `ipinfo.io`, not an in-page `fetch()` from the x.com
origin. A fetch fails with a CORS error.

## 8. Restart gost by hand

```
adb -s <PHONE_TAILNET_IP>:5555 shell 'for p in $(pidof gost); do kill $p; done'
adb -s <PHONE_TAILNET_IP>:5555 shell 'setsid /data/local/tmp/gost -C /data/local/tmp/gost.yaml >/dev/null 2>&1 </dev/null &'
adb -s <PHONE_TAILNET_IP>:5555 shell 'tail -20 /data/local/tmp/gost.log'
```

## 9. After a phone reboot

A reboot keeps the VPN and the gost files, but it closes adb port 5555 and it
kills gost. The watchdog cannot repair this alone. You must open 5555 again
over USB:

1. Connect the phone to a PC with a data USB cable. Unlock the phone and accept
   USB debugging.
2. `adb devices` on that PC must show the phone as `device`.
3. `adb -s <PHONE_SERIAL> tcpip 5555`
4. From the VPS: `adb connect <PHONE_TAILNET_IP>:5555`
5. Start gost with the `setsid` command of section 8.
6. Test with the curl command of section 7.

Keep the USB cable connected. The next reboot then needs no more hardware.

| Sign | Cause | Action |
|---|---|---|
| `adb devices` empty | Charge-only cable, or debugging not accepted | Change the cable. Unlock. Accept the prompt |
| `unauthorized` | New PC key | On the phone, allow USB debugging, tick Always |
| `adb connect` refused | `tcpip 5555` did not hold, or the VPN is down | Do `tcpip` again. Ping the phone on the tailnet |
| curl shows the VPS IP | gost does not listen | Do the `setsid` command again. Check `pidof gost` |

## 10. Security rules

- gost binds the tailnet address only. The proxy ports are not on the internet.
- Keep the config file at mode 600. Other applications cannot read it.
- Never put the password in a command line. Other processes can read `/proc`.
- Wireless debugging is off. adb 5555 comes only from `tcpip` over USB.
- Keep the real values in `.env`. Keep `.env` out of git.
