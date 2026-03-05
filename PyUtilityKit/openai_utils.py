# Importe os pacotes necessários.
# Na verdade, você deve importar apenas as partes necessárias de uma biblioteca,
# mas para este código, assumimos que OpenAI é importado corretamente.
from openai import OpenAI


def generate_response(api_key, openai_model, system_prompt_text, user_prompt_text, temperature, response_format):
    """
    Esta função envia uma solicitação para a API do OpenAI com um prompt dado e retorna a resposta do modelo.

    Argumentos:
    - prompt_text: Uma string contendo o texto do prompt para o qual você deseja uma completude da IA.

    Retorna:
    - O conteúdo da resposta gerada pelo modelo.
    """

    try:
        # Inicialize o cliente OpenAI com sua chave de API.
        # Isso permite que você use vários modelos fornecidos pelo OpenAI.
        openai_client = OpenAI(api_key=api_key)

        # Cria uma resposta usando o cliente da API OpenAI para o chat
        response = openai_client.chat.completions.create(
            model= openai_model, 
             
            messages=[
                {"role": "system", "content": system_prompt_text},
                {"role": "user", "content": user_prompt_text}
            ],

            # max_tokens=max_tokens,  
            temperature=temperature,
            response_format = response_format
        )

        # Extraia o texto gerado da resposta
        # Navegar através da estrutura do objeto de resposta para encontrar o conteúdo relevante
        returned_text = response.choices[0].message.content.strip()

        # Retorne a resposta do modelo para outros usos no programa
        return returned_text

    except Exception as e:
        # Lidar com exceções que podem ocorrer durante a solicitação da API
        # Isso pode incluir problemas de rede, chave de API inválida, etc.
        print("Ocorreu um erro:", str(e))
        return None




# Verifica se o script está sendo executado como o programa principal
if __name__ == "__main__":

    # Chave de API. Isso permite que você use vários modelos fornecidos pelo OpenAI.
    api_key='sk-'  # Certifique-se de substituir por uma chave de API válida.

    # Especifica o modelo de linguagem a ser utilizado. 
    # Neste caso, é uma variante do GPT-4 otimizada para chat. 
    # Modelos diferentes podem ter capacidades e custos diferentes.
    openai_model = "gpt-4o-2024-08-06"

    # Define o número máximo de tokens (palavras ou fragmentos de palavras) que a resposta gerada pode ter. 
    # Limitar tokens ajuda a controlar custos e evita respostas excessivamente longas. 
    # Um 'token' aqui é uma unidade básica que compõe o texto.
    max_tokens = None

    # Controla o nível de "criatividade" ou "aleatoriedade" na resposta gerada.
    # Valores mais baixos (como 0.2) resultam em respostas mais determinísticas e retilíneas.
    # Valores mais altos (próximo de 1) tornam a saída mais variada e imprevisível.
    # Um valor como 0.7 geralmente equilibra bem qualidade e diversidade nas respostas.
    temperature = 0.1

    # Defina os prompts para testar a função
    # A lista 'messages' contém a sequência de mensagens que compõem o contexto da conversa.
    # Cada mensagem tem um papel ('role') e um conteúdo ('content').
    # 'role': 'system' fornece instruções gerais ou estabelece o tom para o assistente.
    # 'role': 'user' contém a interação entrada pelo usuário, geralmente uma pergunta ou comando.
    system_prompt_text = "Você é um assistente prestativo."
    user_prompt_text = "Encontre neste XML as seguintes informações:\
        - CNPJ do emissor da nota fiscal\
        - Nome ou razão social\
        - Número da nota fiscal\
        - Data e hora da emissão\
        - Código de verificação ou chave de acesso\
        Gostaria que você localize os valores e dê resposta no formato JSON. Não preciso de código Python, apenas os valores dos campos desejados e nenhuma explicação adicional.\
        ================================================="

    from pathlib import Path
    xml = Path('/home/eduardo/Desktop/git-repos/automatiza/vGNJjILOi64nlJ8hIibKJ1YXze7kwVCp.xml').read_text()

    user_prompt_text = user_prompt_text + xml


    # O parâmetro response_format da API da OpenAI é usado para especificar o formato desejado da resposta retornada pela API.
    # Esse formato define como a resposta gerada pelo modelo será estruturada e apresentada ao usuário. 
    # A seguir, descrevo algumas opções comuns que podem estar disponíveis para o parâmetro response_format e o que cada uma significa.
    #
    # plaintext: Este formato retorna a resposta em texto puro. É uma escolha simples e direta que geralmente não inclui qualquer tipo de metadata ou formatação adicional. 
    # Ideal para quando você só precisa do texto gerado sem informação adicional.
    #
    # json: Quando o response_format está definido como json, a resposta será estruturada como um objeto JSON.
    # Isso pode incluir não apenas o texto gerado, mas também metadados adicionais, como tokens usados, tempo de resposta, ou qualquer outra informação relevante que a API possa fornecer.
    # Esse formato é particularmente útil para desenvolvedores que precisam integrar a resposta em aplicações que trabalham com dados estruturados.
    #
    # xml: Algumas APIs podem também oferecer respostas no formato XML. Este formato é similar ao JSON em termos de estruturação de dados, mas usa uma sintaxe diferente baseada em tags.
    # É menos comum hoje em dia para APIs modernas, mas ainda pode ser preferido em algumas arquiteturas legadas.
    # 
    # html: Em alguns casos, você pode querer receber a resposta em HTML, especialmente se a intenção for exibir o resultado diretamente em uma página web sem processamento adicional.
    # O formato HTML permite incorporar facilmente o texto gerado em um conteúdo web.

    # Structured Outputs is a new capability in the Chat Completions API and Assistants API that guarantees the model will always generate responses that adhere to your supplied JSON Schema. 
    # https://cookbook.openai.com/examples/structured_outputs_intro
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "math_reasoning",
            "schema": {
                "type": "object",
                "properties": {
                    "codigo_verificacao_e_chave_de_acesso":{
                        "type":"string",
                        "description": "É um código gerado automaticamente pelo sistema fiscal para cada nota fiscal eletrônica. Este código garante a autenticidade e unicidade do documento."
                    },
                    "data_e_hora_da_emissao_da_nfse":{
                        "type":"string",
                        "description": "Indica precisamente quando a nota fiscal foi gerada. Inclui tanto a data completa (dia, mês, ano) quanto a hora (horas e minutos)."
                    },
                    "numero_nota_fiscal":{
                        "type":"string",
                        "description": "Este é um número sequencial único que identifica cada nota fiscal emitida por uma empresa. É gerado de acordo com a ordem de emissão."
                    },
                    "cnpj":{
                        "type":"string",
                        "description": "O CNPJ é um número único atribuído pela Receita Federal do Brasil a cada empresa registrada no Brasil. O número possui 14 dígitos no formato XX.XXX.XXX/0001-XX, onde os primeiros oito dígitos identificam a empresa propriamente dita, os quatro seguintes (0001) referem-se à filial (sendo que a matriz é sempre 0001), e os dois últimos são dígitos de verificação."
                    },
                    "nome_razao_social":{
                        "type":"string",
                        "description": "Este campo indica o nome oficial da empresa que está emitindo a nota, ou em caso de pessoa física, o nome completo. Permite a identificação e reconhecimento da entidade ou pessoa que realizou a venda ou prestação de serviço."
                    },
                    "valor_liquido_da_nfse":{
                        "type":"string",
                        "description": "Representa o valor total dos produtos ou serviços vendidos, descontados quaisquer abatimentos, descontos ou deduções aplicáveis."
                    }
                },
                "required": ["codigo_verificacao_e_chave_de_acesso", "data_e_hora_da_emissao_da_nfse", "numero_nota_fiscal", "cnpj", "nome_razao_social", "valor_liquido_da_nfse"],
                "additionalProperties": False
            },
            "strict": True
        }
    }


    # Chame a função de geração de resposta e capture seu resultado
    result = generate_response(api_key, openai_model, system_prompt_text, user_prompt_text, temperature, response_format)

    # Verifique se obtivemos uma resposta válida e imprima um resultado final
    if result:
        print(result)
    else:
        print("Falha ao obter uma resposta do modelo.")



