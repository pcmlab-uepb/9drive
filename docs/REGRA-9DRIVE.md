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
`http://localhost:4000` · banco no volume Docker `9drive_mysql_data` · backup diário às 3h20 em
`~/Yandex.Disk/9drive-backups` (pasta **sincronizada**; `Pesquisa` não sincroniza).
Nunca marcar a pasta do projeto como "Nuvem" no Gerenciador do Yandex.Disk — o *Aplicar* **apaga a
cópia local** (perda real em 12/10/2026).

**Recuperação em computador novo (perdi esta máquina):**
```bash
git clone https://github.com/pcmlab-uepb/9drive.git ~/9drive
cd ~/9drive && bash scripts/instalar-regra-9drive.sh    # repõe ESTA regra em todos os arquivos do harness
cp .env.docker.example .env.docker                      # preencher segredos (ou recuperar dos containers)
docker compose --env-file .env.docker up -d --build     # painel em http://9drive.localhost
```
Guia completo e histórico das alterações: `FORK-NOTES.md` no repositório.
Manutenção do dia a dia (OAuth, contas, backup): skill `9drive-drive-pool`.
<!-- REGRA-9DRIVE:fim -->
