# Fork local — PCM Lab / UEPB

Este repositório é um fork de [zenhosta/9drive](https://github.com/zenhosta/9drive) mantido pelo
PCM Lab (UEPB) para uso interno: pool de várias contas Google Drive num painel único.

## Alterações em relação ao upstream

| Arquivo | Alteração | Motivo |
|---|---|---|
| `backend/src/modules/auth/auth.routes.ts` | removido `include_granted_scopes: true` | O Google somava escopos já concedidos na conta (YouTube, `drive.file`) ao pedido e devolvia `400 invalid_request: scopes that cannot be requested together`, bloqueando o login. |
| `backend/src/modules/connected-accounts/connected-account.routes.ts` | mesma remoção | Idem, no fluxo de conectar uma nova conta. |
| `backup-9drive.sh` | novo | Dump diário do MySQL (gzip, retenção de 14) para pasta sincronizada, agendado no crontab do usuário. |
| `.gitignore` | `+ .env.docker`, `+ backups/` | Impede que segredos de deploy e dumps do banco entrem no git. |

## Deploy

```bash
cp .env.docker.example .env.docker   # preencher segredos e credenciais Google
docker compose --env-file .env.docker up -d --build
```

O `--env-file` é obrigatório (o compose lê `.env` por padrão). Migrações do Prisma e a semeadura das
credenciais Google (criptografadas no MySQL) rodam na subida do container do backend.

## Acesso

- App: `http://localhost:5173` (frontend) e `http://localhost:4000` (API).

## Notas

- As credenciais OAuth do Google ficam **criptografadas no banco**, semeadas a partir das variáveis
  `GOOGLE_*` do `.env.docker` — nenhum segredo vive neste repositório.
- Escopo solicitado: `drive` (completo) + `userinfo.email` + `userinfo.profile`.
