# **Product Requirements Document (PRD)**

## **Projekt: Dockerized SMTP Relay mit OAuth 2.0 für Outlook**

### **1. Einleitung**
Dieses Projekt zielt darauf ab, ein SMTP-Relay bereitzustellen, das sich über **OAuth 2.0 mit Microsoft Outlook SMTP** (`smtp.office365.com`) authentifiziert. Der Relay-Server läuft in einem **Docker-Container auf Unraid** und wird über eine **Cloudflare-Tunnel-Subdomain (`smtprelay.guggiraid.com`)** erreichbar sein. Gmail wird als Frontend genutzt, um E-Mails über dieses Relay zu senden.

### **2. Ziele & Anforderungen**

#### **2.1 Hauptziele**
- **SMTP-Relay mit OAuth 2.0 für Outlook**
- **Docker-Container für einfache Bereitstellung**
- **Automatische Bereitstellung über GitHub Actions und GHCR**
- **Cloudflare Tunnel für sichere Erreichbarkeit über `smtprelay.guggiraid.com`**
- **Port 587 (TLS) für maximale Kompatibilität mit Gmail**
- **Unraid als Host-Server für den Container**

#### **2.2 Nicht-Ziele**
- Keine Unterstützung für ungesicherte SMTP-Verbindungen (kein Port 25)
- Keine Speicherung von Zugangsdaten im Container (OAuth-Token wird bei Bedarf geholt)

---

### **3. Technischer Überblick**

#### **3.1 Architektur**
1. **Gmail → SMTP-Relay (`smtprelay.guggiraid.com:587`) → Cloudflare Tunnel → Unraid-Server**
2. SMTP-Relay-Container empfängt Mails auf **Port 587** und authentifiziert sich mit **OAuth 2.0 bei Outlook SMTP**.
3. Cloudflare Tunnel leitet Traffic von **`smtprelay.guggiraid.com` auf Port 587** direkt an den Unraid-Server weiter.

#### **3.2 Komponenten**
- **Python SMTP-Relay mit Flask** (OAuth 2.0 Authentifizierung)
- **Docker-Container für den SMTP-Relay**
- **Cloudflare Tunnel für gesicherte externe Erreichbarkeit**
- **GitHub Actions zur automatischen Veröffentlichung in GHCR**
- **Unraid als Host-Umgebung**

#### **3.3 SMTP-Server-Details**
| Einstellung       | Wert                          |
|------------------|-----------------------------|
| **SMTP-Server** | `smtp.office365.com`        |
| **Port**        | `587` (TLS)                  |
| **Authentifizierung** | OAuth 2.0               |
| **Benutzername** | Outlook-E-Mail-Adresse      |
| **Passwort** | Wird durch OAuth-Token ersetzt |

---

### **4. Cloudflare Tunnel Setup**

#### **4.1 Cloudflare DNS-Setup**
- **Subdomain:** `smtprelay.guggiraid.com`
- **Cloudflare Tunnel Mode:** `DNS only (graue Wolke)`

#### **4.2 Cloudflare Tunnel Konfiguration (`config.yml`)**
```yaml
tunnel: smtp-relay
credentials-file: /etc/cloudflared/creds.json

ingress:
  - hostname: smtprelay.guggiraid.com
    service: tcp://192.168.1.100:587
  - service: http_status:404
```

#### **4.3 Cloudflare Tunnel Starten**
```bash
docker restart cloudflare-tunnel
```

---

### **5. Docker-Container Setup**

#### **5.1 Dockerfile**
```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY smtp_relay.py .

EXPOSE 587

CMD ["python", "smtp_relay.py"]
```

#### **5.2 `requirements.txt`**
```
Flask
msal
```

#### **5.3 `docker-compose.yml` für Unraid**
```yaml
version: "3.8"

services:
  smtp-relay:
    image: ghcr.io/dein-ghcr-user/smtp-relay:latest
    container_name: smtp-relay
    ports:
      - "587:587"
    restart: unless-stopped
    environment:
      - CLIENT_ID=DEINE_CLIENT_ID
      - CLIENT_SECRET=DEIN_CLIENT_SECRET
      - TENANT_ID=common
      - USER_EMAIL=deine-outlook-adresse@outlook.com
```

---

### **6. GitHub Actions Workflow für GHCR Deployment**
```yaml
name: Build and Publish Docker Image

on:
  push:
    branches:
      - main

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout Repository
        uses: actions/checkout@v3

      - name: Log in to GitHub Container Registry
        run: echo "${{ secrets.GHCR_TOKEN }}" | docker login ghcr.io -u ${{ github.actor }} --password-stdin

      - name: Build Docker Image
        run: docker build -t ghcr.io/${{ github.repository_owner }}/smtp-relay:latest .

      - name: Push Docker Image to GHCR
        run: docker push ghcr.io/${{ github.repository_owner }}/smtp-relay:latest
```

---

### **7. Gmail SMTP-Einstellungen**
1. **Gehe zu Gmail → Einstellungen → Konten & Import**
2. **„Weitere E-Mail-Adresse hinzufügen“**
3. **SMTP-Server konfigurieren:**
   - **SMTP-Server:** `smtprelay.guggiraid.com`
   - **Port:** `587`
   - **Benutzername:** Deine Outlook-Adresse (`deine-outlook@outlook.com`)
   - **Passwort:** Dummy-Wert (wird nicht genutzt)
   - **TLS aktivieren** ✅
4. **Bestätigungscode eingeben & speichern**

---

## **🎯 Fazit & Vorteile**
✅ **Gmail nutzt Outlook SMTP über OAuth 2.0, ohne dass Basic Auth erforderlich ist**
✅ **Unraid läuft sicher hinter Cloudflare Tunnel**
✅ **Dockerized für einfache Installation & Updates über GHCR**
✅ **Port 587 wird unterstützt, um mit Gmail kompatibel zu sein**

Falls Anpassungen nötig sind, gerne Bescheid geben! 🚀

