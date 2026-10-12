# Fork local — PCM Lab / UEPB

Este repositório é um fork de [zenhosta/9drive](https://github.com/zenhosta/9drive) mantido pelo
PCM Lab (UEPB) para uso interno: pool de várias contas Google Drive num painel único.

## Alterações em relação ao upstream

| Arquivo | Alteração | Motivo |
|---|---|---|
| `backend/src/modules/auth/auth.routes.ts` | removido `include_granted_scopes: true` | O Google somava escopos já concedidos na conta (YouTube, `drive.file`) ao pedido e devolvia `400 invalid_request: scopes that cannot be requested together`, bloqueando o login. |
| `backend/src/modules/connected-accounts/connected-account.routes.ts` | mesma remoção | Idem, no fluxo de conectar uma nova conta. |
| `backup-9drive.sh` | novo | Dump diário do MySQL (gzip, retenção de 14) em `~/Yandex.Disk/9drive-backups` — pasta de **1º nível**, que o daemon do Yandex sincroniza de verdade (`Pesquisa` está em `--exclude-dirs` e não sobe), agendado no crontab do usuário. |
| `frontend/nginx.conf` | bloco `server` para a API + `listen 80 default_server` no bloco da SPA | Permite abrir o app sem porta (`http://9drive.localhost`), com a API num host próprio. O `default_server` é obrigatório: sem ele o primeiro bloco vira o padrão e engole o frontend (404). |
| `docker-compose.yml` | `ports: 80:80` (+`5173:80`) e `frontend/nginx.conf` montado como volume | Endereço sem porta e edição do nginx sem rebuild. |
| `.gitignore` | `+ .env.docker`, `+ backups/` | Impede que segredos de deploy e dumps do banco entrem no git. |

## Deploy

```bash
cp .env.docker.example .env.docker   # preencher segredos e credenciais Google
docker compose --env-file .env.docker up -d --build
```

O `--env-file` é obrigatório (o compose lê `.env` por padrão). Migrações do Prisma e a semeadura das
credenciais Google (criptografadas no MySQL) rodam na subida do container do backend.

## Acesso

| Endereço | O quê |
|---|---|
| `http://9drive.localhost` | painel — endereço do dia a dia (sem porta) |
| `http://api.9drive.localhost` | API (opcional; o painel usa o mesmo caminho `/api` na origem) |
| `http://localhost:5173` | endereço antigo, mantido funcionando |

O app **em produção** chama a API por `/api` na **própria origem** (`src/lib/api.ts`: se `VITE_API_URL`
for o default `http://localhost:4000`, usa `/api`), e o nginx do frontend faz o proxy para o backend —
logo não há CORS envolvido.

`*.localhost` é resolvido para loopback por Chrome e Firefox sem editar `/etc/hosts` (sem sudo).
**Não** use `lvh.me`/`nip.io`/`sslip.io`: o Chrome bloqueia domínios públicos que resolvem para
127.0.0.1 (`net::ERR_BLOCKED_BY_CLIENT`) — o `curl` responde 200 e mascara o problema.

## Onde o projeto vive

Cópia de trabalho: **`~/projetos/9drive`** — **fora** do `~/Yandex.Disk`, de propósito. Segredos em
`.env.docker` (600, no `.gitignore`), com cópia sincronizada em
`~/Yandex.Disk/9drive-backups/.env.docker`. Backups do banco na mesma pasta.

## Recuperação (incidentes de 12/10/2026 — duas vezes no mesmo dia)

A pasta `Pesquisa` está em `--exclude-dirs` do daemon do Yandex.Disk e o *Aplicar* do Gerenciador
(sincronização seletiva) **apaga a cópia local** das pastas marcadas como "Nuvem". A cópia local deste
projeto foi apagada duas vezes; como nada em `Pesquisa` sobe para a nuvem, não havia cópia remota.
Por isso a cópia de trabalho saiu de lá.

Reconstrução: `git clone` daqui + `.env.docker` (da cópia sincronizada ou, na falta dela, das variáveis
dos containers em execução: `docker inspect 9drive-backend-1 9drive-mysql-1`). O banco (volume Docker
`9drive_mysql_data`) nunca foi afetado. **Nunca manter este projeto dentro de `~/Yandex.Disk`.**

## Notas

- As credenciais OAuth do Google ficam **criptografadas no banco**, semeadas a partir das variáveis
  `GOOGLE_*` do `.env.docker` — nenhum segredo vive neste repositório.
- Escopo solicitado: `drive` (completo) + `userinfo.email` + `userinfo.profile`.
