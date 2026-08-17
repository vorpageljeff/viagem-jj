# Bora! — gestão de viagem em grupo

Aplicação full stack para organizar a viagem **Garopaba Réveillon 2026/2027** e criar novas viagens com a mesma estrutura. O MVP conecta participantes, grupos, hospedagens, cenários, votos, orçamento, despesas, rateios e pagamentos sem depender de cálculos financeiros no navegador.

## Arquitetura

```text
frontend (Next.js/TypeScript) → API REST (FastAPI/Pydantic)
                                      ↓
                           serviços de domínio
                         (rateio, saldo, capacidade)
                                      ↓
                         SQLAlchemy → PostgreSQL
                                      ↓
                                  Alembic
```

- `frontend/`: App Router, componentes reutilizáveis, cliente HTTP autenticado e layout responsivo.
- `backend/app/routes/`: endpoints REST e autorização por viagem.
- `backend/app/services/`: regras financeiras e de capacidade, independentes da interface.
- `backend/app/models/`: entidades e vínculos SQLAlchemy.
- `backend/alembic/`: migração inicial versionada.
- `backend/tests/`: testes das regras de rateio, saldo e capacidade.

## Tecnologias

- Next.js 16, React 19 e TypeScript
- Python 3.11, FastAPI, Pydantic 2 e SQLAlchemy 2
- PostgreSQL 16 e Alembic
- JWT local com senha bcrypt
- Docker Compose para desenvolvimento
- Frontend preparado para Vercel; API preparada para Render; banco compatível com Supabase PostgreSQL

JWT foi escolhido no MVP por reduzir configuração externa. Em produção, use um `JWT_SECRET` aleatório, HTTPS e uma senha administrativa forte. Considere Supabase Auth quando o fluxo exigir convite, recuperação de senha e provedores sociais.

## Banco e regras principais

O schema implementado contém:

- `users`, `trips`, `trip_members`: autenticação, viagem e papéis `ADMIN`, `ORGANIZER`, `PARTICIPANT`;
- `participants`, `groups`, `group_participants`: pessoa única por viagem e grupos flexíveis;
- `accommodations`, `rooms` e vínculos de ocupação;
- `accommodation_scenarios`, itens e `scenario_votes`;
- `vehicles` e passageiros;
- `expenses`, `expense_allocations`, `payments` e `budget_items`.

Alocações usam `Decimal`/`Numeric(12,2)`. O backend divide o valor em centavos, distribui o resíduo de forma determinística e garante que a soma das parcelas seja exatamente o valor da despesa. Despesas `CLOSED` não podem ser recalculadas. Desistência altera o status e oferece uma prévia; despesas e pagamentos não são apagados.

## Subir tudo com Docker

Na raiz:

```bash
docker compose up --build
```

Acesse:

- Aplicação: http://localhost:3000
- Swagger: http://localhost:8000/docs
- Health check: http://localhost:8000/health

O container da API executa migrações e seed automaticamente. O seed é idempotente.

### Usuário de desenvolvimento

```text
E-mail: admin@viagem.com
Senha:  viagem2026
```

## Execução manual

### 1. Variáveis de ambiente

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

No PowerShell, use `Copy-Item` no lugar de `cp`. Nunca versionar os arquivos `.env`.

### 2. PostgreSQL

```bash
docker compose up -d db
```

### 3. Backend

```bash
cd backend
python -m venv .venv
# PowerShell: .\.venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload
```

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

### 5. Testes e build

```bash
cd backend
pytest -q

cd ../frontend
npm run build
npm audit --omit=dev
```

## Endpoints principais

- `POST /api/auth/login`, `POST /api/auth/register`, `GET /api/auth/me`
- `GET|POST /api/trips`, `GET|PUT /api/trips/{trip_id}`
- `GET|POST|PUT /api/trips/{trip_id}/participants`
- `GET /participants/{id}/withdrawal-preview`, `POST /participants/{id}/withdraw`
- `GET|POST /api/trips/{trip_id}/groups`, `PUT /groups/{id}/participants`
- `GET|POST /api/trips/{trip_id}/accommodations` e vínculo/desvínculo de pessoas
- `GET|POST /api/trips/{trip_id}/scenarios`, `PUT /scenarios/{id}/vote`
- `GET|POST /api/trips/{trip_id}/expenses`
- `GET|POST /api/trips/{trip_id}/payments`
- `GET|POST /api/trips/{trip_id}/budget`
- `GET /api/trips/{trip_id}/dashboard`

O Swagger em `/docs` contém os contratos e validações atualizados.

## Deploy

### Vercel

1. Importe o repositório e defina `frontend` como Root Directory.
2. Configure `NEXT_PUBLIC_API_URL=https://sua-api.onrender.com/api`.
3. Use o comando de build padrão `npm run build`.

### Render

1. Crie um Blueprint a partir do `render.yaml` da raiz.
2. Informe `DATABASE_URL` com a conexão direta do Neon e escolha uma senha forte para `SEED_ADMIN_PASSWORD`.
3. O Blueprint cria um Web Service gratuito, gera `JWT_SECRET`, executa migrations e cria os dados iniciais de forma idempotente.

### Neon PostgreSQL

1. Crie um projeto gratuito e copie a connection string direta.
2. Troque o prefixo para `postgresql+psycopg://` se necessário.
3. Defina o resultado como `DATABASE_URL` durante a criação do Blueprint no Render.
4. O container executa `alembic upgrade head` antes de iniciar a API.

## Escopo entregue e próxima fase

O MVP prioritário está funcional. Veículos e quartos já existem no domínio para sustentar vínculos e testes de capacidade, mas suas telas administrativas entram na fase seguinte. Alimentação, compras, checklist, agenda, parcelas e fluxo de reembolso ainda não foram implementados; não há telas falsas para esses módulos.
