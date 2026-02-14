#!/usr/bin/env python3
"""
Teste de validação das credenciais do Google Service Account.
"""

import json
import os

def validate_credentials():
    """Testa se as credenciais estão correIras."""

    # Tentar ler de arquivos locais
    credentials_files = ['service_account.json', 'service-account.json']

    for cred_file in credentials_files:
        if os.path.exists(cred_file):
            print(f"📂 Arquivo encontrado: {cred_file}")

            with open(cred_file, 'r') as f:
                try:
                    creds = json.load(f)
                    print(f"✅ Parse JSON bem-sucedido")

                    # Verificar campos essenciais
                    required_fields = [
                        'type', 'project_id', 'private_key_id',
                        'private_key', 'client_email', 'client_id'
                    ]

                    missing_fields = []
                    for field in required_fields:
                        if field not in creds:
                            missing_fields.append(field)
                        else:
                            value_preview = str(creds[field])[:50]
                            if field == 'private_key':
                                value_preview = creds[field][:50] + "..."
                            print(f"  ✅ {field}: {value_preview}")

                    if missing_fields:
                        print(f"❌ Campos faltando: {missing_fields}")
                        return False

                    # Verificar private_key
                    private_key = creds['private_key']
                    print(f"\n🔍 Análise da private_key:")
                    print(f"  Tamanho: {len(private_key)} caracteres")
                    print(f"  Começa com: {private_key[:30]}...")

                    # Verificar se tem quebras de linha correIras
                    if 'BEGIN PRIVATE KEY' not in private_key:
                        print(f"❌ ERRO: private_key não começa com 'BEGIN PRIVATE KEY'")
                        return False

                    if 'END PRIVATE KEY' not in private_key:
                        print(f"❌ ERRO: private_key não termina com 'END PRIVATE KEY'")
                        return False

                    print(f"\n✅ Credenciais parecem válidas!")
                    return True

                except json.JSONDecodeError as e:
                    print(f"❌ Erro de parse JSON: {e}")
                    return False
                except Exception as e:
                    print(f"❌ Erro ao ler arquivo: {e}")
                    return False

    print(f"❌ Nenhum arquivo de credenciais encontrado")
    print(f"Procurados: {credentials_files}")
    return False

def test_gspread_connection():
    """Testa a conexão com gspread."""
    try:
        import gspread
        print(f"\n🔧 Testando conexão com gspread...")

        credentials_files = ['service_account.json', 'service-account.json']

        for cred_file in credentials_files:
            if os.path.exists(cred_file):
                print(f"📂 Conectando usando: {cred_file}")

                try:
                    gc = gspread.service_account(filename=cred_file)
                    print(f"✅ gspread.service_account() bem-sucedido!")

                    # Tentar aber uma planilha de teste
                    print(f"📊 Tentando aber planilha 'Journal Database'...")
                    sheet = gc.open('Journal Database')
                    print(f"✅ Planilha aberida com sucesso!")
                    print(f"📋 Título: {sheet.title}")
                    print(f"📋 URL: {sheet.url}")

                    return True

                except Exception as e:
                    print(f"❌ Erro ao conectar: {type(e).__name__}")
                    print(f"   Detalhes: {str(e)}")

                    if 'APIError' in str(type(e).__name__):
                        print(f"\n💡 Possíveis causas:")
                        print(f"   1. Service Account não tem permissão na planilha")
                        print(f"   2. Planilha 'Journal Database' não existe")
                        print(f"   3. API do Google Sheets não está ativada")

                    return False

        print(f"❌ Nenhum arquivo de credenciais encontrado")
        return False

    except ImportError:
        print(f"❌ gspread não instalado")
        print(f"   Instale com: pip install gspread")
        return False

if __name__ == "__main__":
    print("="*60)
    print("🔍 TESTE DE CREDENCIAIS GOOGLE SERVICE ACCOUNT")
    print("="*60)

    # Teste 1: Validar estrutura
    print("\n📋 TESTE 1: Validar estrutura do JSON")
    print("-"*60)
    validate_credentials()

    # Teste 2: Conexão gspread
    print("\n🔧 TESTE 2: Testar conexão com gspread")
    print("-"*60)
    test_gspread_connection()

    print("\n" + "="*60)
    print("✅ Testes concluídos!")
    print("="*60)
