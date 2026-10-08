# Gestão de toner (Django)

Monitora o nível de toner de impressoras de rede via SNMP (Printer MIB), controla estoque e registra trocas.
Acesso restrito ao grupo **TI**.

## Teste rápido (dados simulados)
```bash
python -m venv venv && source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py popular_demo        # cria impressoras fictícias + usuário admin/admin123
TONER_DEMO=1 python manage.py runserver 0.0.0.0:8000
```
Abra http://localhost:8000 e entre com `admin` / `admin123` (**apague esse usuário em produção**).

## Uso real
1. `sudo apt install snmp` (o coletor usa `snmpwalk`) e habilite SNMP nas impressoras.
2. `python manage.py createsuperuser`
3. Em `/admin/`: crie o grupo **TI**, adicione os usuários da equipe e cadastre impressoras (IP, setor, community) e modelos de toner.
4. Agende a coleta (cron, a cada 30 min):
   `*/30 * * * * cd /opt/toner_manager && venv/bin/python manage.py coletar_toner`
5. O botão "Coletar agora" no painel faz o mesmo manualmente.

## Variáveis de ambiente
| Variável | Padrão | Função |
|---|---|---|
| `DJANGO_SECRET_KEY` | inseguro | **defina em produção** |
| `DJANGO_DEBUG` | 1 | use 0 em produção |
| `DJANGO_ALLOWED_HOSTS` | * | ex.: `toner.empresa.local` |
| `TONER_LIMITE_ALERTA` | 15 | % que dispara alerta |
| `TONER_SALTO_TROCA` | 30 | aumento de % que conta como troca |
| `TONER_ALERTA_EMAILS` | vazio | destinatários separados por vírgula |
| `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT` | console | envio de e-mail (SMTP) |
| `TONER_DEMO` | 0 | 1 = dados simulados |

## Produção
Use `gunicorn config.wsgi` atrás de Nginx com HTTPS interno, restrinja por firewall à rede da TI e rode `collectstatic` se servir o admin por Nginx.
Para Active Directory, adicione `django-auth-ldap` (AUTHENTICATION_BACKENDS) e mapeie o grupo do AD para `TI`.
