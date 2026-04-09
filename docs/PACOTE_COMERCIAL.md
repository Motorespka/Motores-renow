# Pacote Comercial (Acesso)

## Regras ativas no app

- `Free (teaser)`
  - Pode fazer login.
  - Pode abrir `Consulta` em modo limitado.
  - Nao pode abrir `Diagnostico`.
  - Nao pode abrir `Cadastro`, salvo liberacao manual do admin.

- `Pago` (`plan` em `paid`, `pro`, `premium`, `enterprise`, `business`)
  - Pode abrir `Consulta` completa.
  - Pode abrir `Cadastro`.
  - Pode abrir `Diagnostico` e `Detalhe`.

- `Admin` (`role = 'admin'` e `ativo = true`)
  - Tudo do plano pago.
  - Pode abrir `Edit`.
  - Pode abrir `Admin` (painel de configuracao).
  - Pode liberar/remover permissao manual de cadastro.

## Fluxo comercial recomendado

1. Usuario cria conta e entra no modo `Free (teaser)`.
2. Usuario conhece o catalogo em visualizacao limitada.
3. Quando pagar, admin muda o `plan` para `paid`.
4. Se quiser teste rapido sem pagar, admin pode liberar apenas `Cadastro` manualmente.

## Painel admin no site

- Menu lateral mostra botao `Admin` apenas para usuario admin.
- Dentro do painel voce consegue:
  - Buscar usuario.
  - Alterar `username`, `nome`, `role`, `plan` e `ativo`.
  - Liberar/remover permissao manual de cadastro.

## SQL rapido para liberar plano pago

```sql
update public.usuarios_app
set plan = 'paid',
    ativo = true,
    updated_at = now()
where lower(email) = lower('cliente@exemplo.com');
```

## SQL rapido para voltar para free

```sql
update public.usuarios_app
set plan = 'free',
    updated_at = now()
where lower(email) = lower('cliente@exemplo.com');
```
