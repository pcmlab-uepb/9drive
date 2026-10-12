<!-- REGRA-9DRIVE:inicio (instalada por scripts/instalar-regra-9drive.sh — não editar à mão) -->
## REGRA 9Drive — armazenamento em nuvem e âncora de recuperação do harness

**O que é:** pool das contas Google Drive (PCM Lab/UEPB) num painel único; cada upload vai para a conta
com espaço livre (cotas em TB). Dois papéis: (1) armazenamento dos artefatos grandes que não cabem no
disco local; (2) **âncora de recuperação** — o repositório público `github.com/pcmlab-uepb/9drive`
guarda o serviço **e o instalador desta regra**.

**Quando usar (obrigatório):** arquivo, figura, dataset, PDF, vídeo, dump ou material de apoio grande →
subir pelo painel e **referenciar por link** no documento/entrega, em vez de anexar. Antes de gerar
artefatos pesados, conferir o *Quota Tracker* do painel. Credencial do pool nunca em texto: os tokens
ficam criptografados no banco do serviço.

**Acesso:** `http://9drive.localhost` (atalho "9Drive" no menu e na área de trabalho) · API interna
`http://localhost:4000` e `https://localhost` (TLS local, usado no redirect do Google).
**Pasta montada:** **`~/Drive`** — o Google Drive da conta principal montado como pasta comum
(rclone; serviço de usuário `rclone-9drive.service`, sobe no login). Para copiar/abrir arquivo sem
passar pelo painel, use essa pasta; escrita direta funciona (sobe ao fechar o arquivo).
Código de trabalho: **`~/projetos/9drive`** (fora do Yandex.Disk) · segredos
`~/projetos/9drive/.env.docker` (600, nunca versionado) · cópia dos segredos **sincronizada** em
`~/Yandex.Disk/9drive-backups/.env.docker` · backup do banco às 3h20 em `~/Yandex.Disk/9drive-backups/`
(retenção 14 dias).

**Google (app OAuth publicado):** status **"Em produção"** desde 12/10/2026 (fim da reautorização a
cada 7 dias), projeto `fq2-materiais-261011`, cliente Web "9Drive" com redirect
`https://localhost/connected-accounts/google/callback` — **somente HTTPS**: o Google recusa publicar
enquanto houver qualquer URI de redirecionamento/origem HTTP no cliente.
Página pública e política de privacidade (exigidas para publicar): **https://pcmlab-uepb.github.io/9drive/**
e **.../privacy.html** (fonte em `docs/`, publicadas pelo GitHub Pages do repositório).
Certificado TLS local: `certs/` (fora do git) — regerar com `bash scripts/gerar-certificado.sh`.
Ao conectar contas: a tela de consentimento é do app publicado (pode exibir aviso de app não verificado,
pois o escopo `drive` é restrito e não passou pela verificação do Google).

**⚠️ Nunca manter a cópia de trabalho dentro de `~/Yandex.Disk`.** A pasta `Pesquisa` está em
`--exclude-dirs` (nada dela sobe para a nuvem) e o botão *Aplicar* do Gerenciador do Yandex.Disk
**apaga a cópia local** das pastas marcadas como "Nuvem": apagou este projeto **duas vezes** em
12/10/2026. O Yandex.Disk guarda só os backups; o código vive em `~/projetos` + GitHub.

**Recuperação em computador novo (perdi esta máquina):**
```bash
git clone https://github.com/pcmlab-uepb/9drive.git ~/projetos/9drive
cd ~/projetos/9drive
bash scripts/instalar-regra-9drive.sh                    # repõe ESTA regra em todos os arquivos do harness
cp ~/Yandex.Disk/9drive-backups/.env.docker .env.docker  # segredos sincronizados (se houver cópia)
# sem cópia: cp .env.docker.example .env.docker e preencher
docker compose --env-file .env.docker up -d --build      # painel em http://9drive.localhost
```
Guia completo e histórico das alterações: `FORK-NOTES.md` no repositório.
Manutenção do dia a dia (OAuth, contas, backup): skill `9drive-drive-pool`.
<!-- REGRA-9DRIVE:fim -->
