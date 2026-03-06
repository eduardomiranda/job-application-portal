import streamlit as st
import re
import os
import io
import importlib
import tempfile
import zipfile
from html import escape
from datetime import datetime
from zoneinfo import ZoneInfo

from PyUtilityKit.email_utils import enviar_html_email
from PyUtilityKit.mongo_utils import salva_no_mongo


def _parse_recipients(value):
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def _now_iso(timezone):
    if timezone:
        try:
            return datetime.now(ZoneInfo(timezone)).isoformat()
        except Exception:
            pass
    return datetime.utcnow().isoformat() + "Z"


def _to_text(value):
    return str(value).replace("\n", " ").strip()


def _markdown_to_plain_text(markdown_text):
    if not markdown_text:
        return ""

    text = str(markdown_text)
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"^\s{0,3}#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1 (\2)", text)
    text = re.sub(r"^\s*[-*+]\s+", "- ", text, flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _markdown_to_html(markdown_text):
    if not markdown_text:
        return ""

    try:
        markdown_module = importlib.import_module("markdown")
        return markdown_module.markdown(
            markdown_text,
            extensions=["extra", "nl2br", "sane_lists"],
        )
    except Exception:
        escaped = escape(markdown_text)
        escaped = re.sub(r"^\s{0,3}#{1,6}\s*(.+)$", r"<h4>\1</h4>", escaped, flags=re.MULTILINE)
        escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
        escaped = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", escaped)
        escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
        escaped = re.sub(r"^\s*[-*+]\s+(.+)$", r"• \1", escaped, flags=re.MULTILINE)
        return escaped.replace("\n", "<br>")


def _apply_executive_email_styles(html_fragment):
    if not html_fragment:
        return ""

    styled = html_fragment
    replacements = {
        "<h1>": '<h1 style="margin:16px 0 4px 0; font-size:22px; line-height:1.3; color:#0f172a;">',
        "<h2>": '<h2 style="margin:14px 0 4px 0; font-size:20px; line-height:1.3; color:#0f172a;">',
        "<h3>": '<h3 style="margin:12px 0 4px 0; font-size:18px; line-height:1.35; color:#0f172a;">',
        "<h4>": '<h4 style="margin:10px 0 4px 0; font-size:16px; line-height:1.4; color:#0f172a;">',
        "<h5>": '<h5 style="margin:10px 0 4px 0; font-size:15px; line-height:1.4; color:#0f172a;">',
        "<h6>": '<h6 style="margin:10px 0 4px 0; font-size:14px; line-height:1.4; color:#0f172a;">',
        "<p>": '<p style="margin:0 0 10px 0; font-size:14px; line-height:1.6;">',
        "<ul>": '<ul style="margin:4px 0 12px 20px; padding:0;">',
        "<ol>": '<ol style="margin:4px 0 12px 20px; padding:0;">',
        "<li>": '<li style="margin:0 0 6px 0; line-height:1.6;">',
        "<strong>": '<strong style="color:#0f172a;">',
        "<blockquote>": '<blockquote style="margin:10px 0; padding:8px 12px; border-left:3px solid #d0d7de; color:#374151;">',
    }

    for source, target in replacements.items():
        styled = styled.replace(source, target)

    return styled


def _secret_text(section, key, default=""):
    section_data = st.secrets.get(section, {})
    value = section_data.get(key, default)
    if isinstance(value, str):
        return value.strip()
    return value


def _extract_text_from_pdf_bytes(file_bytes):
    parser_errors = []
    try:
        pypdf_module = importlib.import_module("pypdf")
        PdfReader = getattr(pypdf_module, "PdfReader")
        reader = PdfReader(io.BytesIO(file_bytes))
        return "\n".join((page.extract_text() or "") for page in reader.pages).strip(), "pypdf", parser_errors
    except Exception as ex:
        parser_errors.append(f"pypdf: {ex}")
        try:
            pypdf2_module = importlib.import_module("PyPDF2")
            PdfReader = getattr(pypdf2_module, "PdfReader")
            reader = PdfReader(io.BytesIO(file_bytes))
            return "\n".join((page.extract_text() or "") for page in reader.pages).strip(), "PyPDF2", parser_errors
        except Exception as inner_ex:
            parser_errors.append(f"PyPDF2: {inner_ex}")
            return "", "none", parser_errors


def _extract_text_from_docx_bytes(file_bytes):
    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
            xml = zf.read("word/document.xml").decode("utf-8", errors="ignore")
        text = re.sub(r"<[^>]+>", " ", xml)
        text = re.sub(r"\s+", " ", text)
        return text.strip()
    except Exception:
        return ""


def _log_resume_extraction(file_name, source, extracted_text, errors=None):
    text_length = len(extracted_text or "")
    print("[resume-extract] ------------------------------")
    print(f"[resume-extract] arquivo: {file_name}")
    print(f"[resume-extract] parser: {source}")
    print(f"[resume-extract] caracteres_extraidos: {text_length}")

    if errors:
        for err in errors:
            print(f"[resume-extract] erro_parser: {err}")

    preview_limit = 3000
    preview = (extracted_text or "")[:preview_limit]
    print("[resume-extract] texto_extraido_inicio")
    print(preview if preview else "<VAZIO>")
    if text_length > preview_limit:
        print("[resume-extract] ... texto truncado para preview ...")
    print("[resume-extract] texto_extraido_fim")
    print("[resume-extract] ------------------------------")


def _extract_resume_text(uploaded_file):
    if uploaded_file is None:
        return ""

    file_name = (uploaded_file.name or "").lower()
    file_bytes = uploaded_file.getvalue()

    if file_name.endswith(".pdf"):
        extracted_text, parser_name, parser_errors = _extract_text_from_pdf_bytes(file_bytes)
        # _log_resume_extraction(file_name, parser_name, extracted_text, parser_errors)
        return extracted_text

    if file_name.endswith(".docx"):
        extracted_text = _extract_text_from_docx_bytes(file_bytes)
        # _log_resume_extraction(file_name, "docx-xml", extracted_text)
        return extracted_text

    if file_name.endswith(".doc"):
        extracted_text = file_bytes.decode("latin-1", errors="ignore").strip()
        # _log_resume_extraction(file_name, "doc-latin1", extracted_text)
        return extracted_text

    extracted_text = file_bytes.decode("utf-8", errors="ignore").strip()
    # _log_resume_extraction(file_name, "utf8-generic", extracted_text)
    return extracted_text


def _job_description_text():
    return """
Título da vaga: 📢 Analista de Implementação Técnica (PrivacyOps)
Sobre a Função
- Buscamos um profissional com forte viés tecnológico para atuar na configuração, integração e sustentação de plataforma em nossos clientes. Seu objetivo principal é garantir que a automação de privacidade funcione tecnicamente, conectando a plataforma aos ecossistemas de dados (SaaS, On-premise, Cloud) dos clientes.

Responsabilidades e Atribuições 
- Configuração de Conectores: Configurar e validar conectores de plataformas de privacidade com diversas fontes de dados (Bancos de dados SQL/NoSQL, CRMs, ERPs e ambientes Cloud como AWS/Azure/GCP).
- Automação de Varreduras (Data Discovery): Configurar políticas de escaneamento para identificação de dados sensíveis e classificação automatizada de ativos.
- Orquestração de Workflows: Desenvolver e testar fluxos de automação para atendimento de direitos de titulares (DSAR) e gestão de consentimento.
- Integrações via API: Atuar na integração da plataforma com outros sistemas via APIs e Webhooks para garantir a fluidez dos processos de privacidade.
- Troubleshooting: Realizar o diagnóstico e a correção de falhas de comunicação entre a plataforma e as fontes de dados dos clientes.
- Customização de Portais: Configurar centros de preferência e banners de cookies conforme as especificações técnicas e de design.

Requisitos e Qualificações 
- Configuração de Sistemas: Experiência sólida na configuração de softwares complexos, plataformas SaaS ou ferramentas de governança de dados (Securiti, OneTrust, BigID, etc).
- Domínio de Plataformas de Privacidade: Experiência técnica em implantação e sustentação de ferramentas de privacidade.
- Conhecimento em Infraestrutura e Nuvem: Noções de ambientes Cloud e conectividade (firewalls, permissões de acesso, redes).
- Bancos de Dados: Conhecimento básico em consultas SQL para validação de conexões e fluxos de dados.
- Perfil de Consultor Técnico: Capacidade de dialogar com os times de TI/Infraestrutura dos clientes para viabilizar às integrações.

Diferenciais 
- Desenvolvimento: Noções de JavaScript, Python ou Shell Script para automação de tarefas, embora não seja uma vaga de coding, o conhecimento nas linguagens agrega muito valor na criação de automações customizadas
- Privacidade de Dados: Conhecimento da LGPD/GDPR sob a ótica de implementação técnica.
- Segurança da Informação: Conhecimento em autenticação (SAML, OAuth, SSO) e criptografia.
- Formação Acadêmica: Graduação ou cursos técnicos em TI, Redes, Ciência da Computação ou áreas correlatas.
""".strip()


def _build_recruiter_prompt():
    return """
Você é um recrutador sênior de uma consultoria de tecnologia especializada em contratação de profissionais de TI (engenharia de dados, cloud, software, DevOps, analytics e AI).
Sua tarefa é avaliar um currículo em relação a uma descrição de vaga e produzir uma análise objetiva e profissional.

Instruções

Analise cuidadosamente:
A descrição da vaga
O currículo do candidato
Avalie o nível de aderência considerando:
Competências técnicas
Experiência profissional relevante
Experiência com ferramentas e tecnologias exigidas
Senioridade
Experiência em projetos similares
Experiência em cloud / big data / engenharia de software (quando aplicável)
Clareza e qualidade do currículo

Gere uma nota de aderência de 0 a 10, onde:
0–3 = Muito fraco
4–5 = Parcialmente aderente
6–7 = Bom alinhamento
8–9 = Muito forte
10 = Candidato ideal

Produza a resposta com a seguinte estrutura:

1. Nota geral: Nota de aderência do candidato à vaga (0–10)
2. Pontos fortes do candidato: Liste os principais pontos positivos em relação à vaga.
3. Lacunas ou pontos de atenção: Liste o que está faltando ou pode ser considerado fraco.
4. Avaliação técnica
Avalie especificamente:
Stack tecnológica
Experiência prática
Aderência às tecnologias da vaga

5. Avaliação de senioridade
Indique se o candidato parece:
Júnior
Pleno
Sênior
Especialista

E se está acima, adequado ou abaixo do nível da vaga.

6. Recomendação do recrutador
Escolha uma opção e explique brevemente:
❌ Não recomendar entrevista
⚠️ Entrevista opcional
✅ Recomendar entrevista
⭐ Forte candidato

7. Sugestões para melhorar o currículo: Dê sugestões práticas para que o candidato melhore o currículo para vagas semelhantes.
""".strip()


def _generate_openai_response(api_key, openai_model, system_prompt_text, user_prompt_text, temperature, response_format):
    openai_utils_module = importlib.import_module("PyUtilityKit.openai_utils")
    generator = getattr(openai_utils_module, "generate_response")
    return generator(
        api_key=api_key,
        openai_model=openai_model,
        system_prompt_text=system_prompt_text,
        user_prompt_text=user_prompt_text,
        temperature=temperature,
        response_format=response_format,
    )

PAGE_TITLE = "Analista de Implementação Técnica (PrivacyOps)"

st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon="👨‍💻",
    layout="centered",
)

# CSS mínimo apenas para ocultar elementos padrão do Streamlit
st.markdown("""
<style>
[data-testid="stHeader"] { display: none; }
footer { display: none; }
</style>
""", unsafe_allow_html=True)

# ── Cabeçalho ───────────────────────────────────────────────────────────────
job_title = "📢 Analista de Implementação Técnica (PrivacyOps)"

# st.title("📢 Analista de Implementação Técnica (PrivacyOps)")
st.caption("Century Data · Híbrido · Tempo integral")

tab_overview, tab_application = st.tabs(["📋 Visão Geral", "📝 Candidatura"])

# ── Aba Visão Geral ──────────────────────────────────────────────────────────
with tab_overview:
    st.subheader("Sobre a Função")
    st.write(
        "Buscamos um profissional com forte viés tecnológico para atuar na configuração, integração "
        "e sustentação de plataforma em nossos clientes. Seu objetivo principal é garantir que a "
        "automação de privacidade funcione tecnicamente, conectando a plataforma aos ecossistemas de "
        "dados (**SaaS, On-premise e Cloud**) dos clientes."
    )

    st.subheader("Responsabilidades e Atribuições")
    st.markdown("""
- **Configuração de Conectores:** Configurar e validar conectores de plataformas de privacidade com diversas fontes de dados (bancos SQL/NoSQL, CRMs, ERPs e ambientes cloud como AWS/Azure/GCP).
- **Automação de Varreduras (Data Discovery):** Configurar políticas de escaneamento para identificação de dados sensíveis e classificação automatizada de ativos.
- **Orquestração de Workflows:** Desenvolver e testar fluxos de automação para atendimento de direitos de titulares (DSAR) e gestão de consentimento.
- **Integrações via API:** Atuar na integração da plataforma com outros sistemas via APIs e Webhooks para garantir a fluidez dos processos de privacidade.
- **Troubleshooting:** Realizar o diagnóstico e a correção de falhas de comunicação entre a plataforma e as fontes de dados dos clientes.
- **Customização de Portais:** Configurar centros de preferência e banners de cookies conforme as especificações técnicas e de design.
    """)

    st.subheader("Requisitos e Qualificações")
    st.markdown("""
- **Configuração de Sistemas:** Experiência sólida na configuração de softwares complexos, plataformas SaaS ou ferramentas de governança de dados (Securiti, OneTrust, BigID, etc.).
- **Domínio de Plataformas de Privacidade:** Experiência técnica em implantação e sustentação de ferramentas de privacidade.
- **Conhecimento em Infraestrutura e Nuvem:** Noções de ambientes cloud e conectividade (firewalls, permissões de acesso, redes).
- **Bancos de Dados:** Conhecimento básico em consultas SQL para validação de conexões e fluxos de dados.
- **Perfil de Consultor Técnico:** Capacidade de dialogar com os times de TI/Infraestrutura dos clientes para viabilizar as integrações
    """)

    st.subheader("Diferenciais")
    st.markdown("""
- **Desenvolvimento:** Noções de JavaScript, Python ou Shell Script para automação de tarefas; embora não seja uma vaga de coding, o conhecimento agrega valor na criação de automações customizadas.
- **Privacidade de Dados:** Conhecimento da LGPD/GDPR sob a ótica de implementação técnica.
- **Segurança da Informação:** Conhecimento em autenticação (SAML, OAuth, SSO) e criptografia.
- **Formação Acadêmica:** Graduação ou cursos técnicos em TI, Redes, Ciência da Computação ou áreas correlatas.
    """)

    st.info("Pronto(a) para se candidatar? Vá para a aba **Candidatura** acima.")

# ── Aba Candidatura ──────────────────────────────────────────────────────────
with tab_application:
    timezone = _secret_text('system', "timezone", '')

    mongodb_uri = _secret_text('mongodb', 'mongodb_uri', '')
    mongodb_db = _secret_text('mongodb', 'mongodb_db', '')
    mongodb_collection = _secret_text('mongodb', 'mongodb_collection', '')

    sender = _secret_text('email', 'sender', '')
    password = _secret_text('email', 'password', '')
    destinatarios_bcc = _secret_text('email', 'destinatarios_bcc', '')

    openai_api_key = _secret_text('openai', 'api_key', '')
    if not openai_api_key:
        openai_api_key = _secret_text('openai', 'api_kei', '')
    openai_model = _secret_text('openai', 'openai_model', '')

    st.subheader("👤 Informações Pessoais")

    col1, col2 = st.columns(2)
    first_name = col1.text_input("Nome *")
    last_name  = col2.text_input("Sobrenome *")

    email = st.text_input("E-mail *")
    phone = st.text_input("Telefone *")

    col3, col4 = st.columns(2)
    city    = col3.text_input("Cidade")
    country = col4.selectbox("Estado *", [
        "— Selecione —", "Acre", "Alagoas", "Amapá", "Amazonas", "Bahia",
        "Ceará", "Distrito Federal", "Espírito Santo", "Goiás", "Maranhão",
        "Mato Grosso", "Mato Grosso do Sul", "Minas Gerais", "Pará", "Paraíba",
        "Paraná", "Pernambuco", "Piauí", "Rio de Janeiro", "Rio Grande do Norte",
        "Rio Grande do Sul", "Rondônia", "Roraima", "Santa Catarina", "São Paulo",
        "Sergipe", "Tocantins",
    ])

    st.divider()

    # ── Currículo e Links ────────────────────────────────────────────────────
    st.subheader("📄 Currículo e Links")

    resume    = st.file_uploader("Envie seu currículo *", type=["pdf", "doc", "docx"])
    linkedin  = st.text_input("URL do perfil no LinkedIn", placeholder="https://linkedin.com/in/...")
    portfolio = st.text_input("URL do GitHub / Portfólio", placeholder="https://github.com/...")

    st.divider()

    # ── Histórico Técnico ─────────────────────────────────────────────────────
    st.subheader("💻 Histórico Técnico")

    years_exp = st.selectbox("Anos de experiência?", [
        "— Selecione —", "1–2 anos", "3–4 anos", "5–6 anos", "7–9 anos", "10+ anos",
    ])

    privacy_platform_exp = st.radio("Experiência prática com Securiti ou OneTrust? *", [
        "Sim – uso em produção",
        "Sim – projetos pessoais/de estudo",
        "Não, mas tenho familiaridade",
        "Sem experiência",
    ])

    tech_stack = st.text_area(
        "Descreva sua experiência com stack de dados *",
        placeholder="ex.: Securiti, OneTrust, APIs, SQL, AWS/Azure/GCP, automações de privacidade…",
        height=110,
    )

    st.divider()

    col5, col6 = st.columns(2)
    availability = col5.selectbox("Disponibilidade para início *", [
        "— Selecione —", "Imediatamente", "2 semanas", "1 mês", "2 meses", "3+ meses",
    ])
    salary_exp = col6.text_input("Pretensão salarial (mês bruto) *", placeholder="ex.: 6000")

    st.divider()

    # ── Informações Adicionais ───────────────────────────────────────────────
    st.subheader("📋 Informações Adicionais")

    heard_about = st.selectbox("Como você soube desta vaga? *", [
        "— Selecione —", "LinkedIn", "Indeed", "Glassdoor", "Site da empresa",
        "Amigo / Indicação", "Twitter / X", "GitHub", "Outro",
    ])

    additional_notes = st.text_area(
        "Algo mais que você gostaria que soubéssemos?",
        placeholder="Opcional – certificações, contribuições open source, prêmios…",
        height=100,
    )

    agree = st.checkbox(
        "Declaro que todas as informações fornecidas são verdadeiras e completas, e autorizo a Century Data a coletar, armazenar e tratar meus dados pessoais exclusivamente para fins de recrutamento e seleção, em conformidade com a Lei Geral de Proteção de Dados (LGPD – Lei nº 13.709/2018). Estou ciente de que posso solicitar a exclusão dos meus dados a qualquer momento."
    )

    st.divider()

    # ── Envio ────────────────────────────────────────────────────────────────
    submitted = st.button("Enviar Candidatura", type="primary", use_container_width=True)

    if submitted:
        errors = []

        if not first_name.strip():           errors.append("O nome é obrigatório.")
        if not last_name.strip():            errors.append("O sobrenome é obrigatório.")
        if not email.strip() or not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                             errors.append("Um e-mail válido é obrigatório.")
        if not phone.strip():                errors.append("O telefone é obrigatório.")
        if country == "— Selecione —":       errors.append("Selecione seu estado.")
        if resume is None:                   errors.append("Envie seu currículo.")
        if years_exp == "— Selecione —":     errors.append("Selecione seus anos de experiência.")
        if not tech_stack.strip():           errors.append("Descreva sua experiência com stack de dados.")
        if availability == "— Selecione —":  errors.append("Selecione sua disponibilidade.")
        if not salary_exp.strip():           errors.append("Informe sua pretensão salarial.")
        if heard_about == "— Selecione —":   errors.append("Informe como você soube desta vaga.")
        if not agree:                        errors.append("Você deve confirmar o consentimento para enviar.")

        if errors:
            for e in errors:
                st.error(e)
        else:
            application_data = {
                "created_at": _now_iso(timezone),
                "timezone": timezone,
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "phone": phone,
                "city": city,
                "country": country,
                "linkedin": linkedin,
                "portfolio": portfolio,
                "years_exp": years_exp,
                "privacy_platform_exp": privacy_platform_exp,
                "tech_stack": tech_stack,
                "availability": availability,
                "salary_exp": salary_exp,
                "heard_about": heard_about,
                "additional_notes": additional_notes,
                "resume_filename": resume.name if resume else None
            }

            mongo_ok = False
            email_ok = False
            candidate_email_ok = False
            inserted_id = None
            ai_evaluation = ""

            with st.spinner("Processando submissão... isso pode levar alguns segundos."):
                if openai_api_key and openai_model and resume is not None:
                    try:
                        resume_text = _extract_resume_text(resume)
                        if resume_text:
                            evaluation_prompt = (
                                "Descrição da vaga:\n"
                                f"{_job_description_text()}\n\n"
                                "Currículo do candidato:\n"
                                f"{resume_text[:35000]}"
                            )

                            ai_response = _generate_openai_response(
                                api_key=openai_api_key,
                                openai_model=openai_model,
                                system_prompt_text=_build_recruiter_prompt(),
                                user_prompt_text=evaluation_prompt,
                                temperature=0.1,
                                response_format={"type": "text"},
                            )
                            ai_evaluation = ai_response or "Avaliação indisponível (sem retorno da OpenAI)."
                        else:
                            ai_evaluation = "Avaliação indisponível (não foi possível extrair texto do currículo anexado)."
                    except Exception as ex:
                        ai_evaluation = f"Avaliação indisponível (erro OpenAI: {ex})."
                else:
                    ai_evaluation = "Avaliação indisponível (configuração OpenAI ausente, modelo ausente ou currículo não anexado)."

                application_data["ai_evaluation"] = ai_evaluation

                if mongodb_uri and mongodb_db and mongodb_collection:
                    try:
                        inserted_id = str(
                            salva_no_mongo(
                                mongodb_uri,
                                mongodb_db,
                                mongodb_collection,
                                application_data,
                            )
                        )
                        mongo_ok = True
                    except Exception as ex:
                        error_msg = str(ex)
                        st.error(f"Falha ao salvar no MongoDB: {error_msg}")
                        if "bad auth" in error_msg.lower() or "authentication failed" in error_msg.lower():
                            st.warning(
                                "Verifique o `mongodb_uri` no `st.secrets`: usuário/senha corretos, senha URL-encoded "
                                "(ex.: `@` -> `%40`) e `authSource=admin` quando necessário."
                            )
                else:
                    st.error("Configuração de MongoDB ausente em st.secrets.")

                if sender and password:
                    subject = f"Nova candidatura | {first_name} {last_name} | {job_title}"
                    ai_evaluation_plain = _markdown_to_plain_text(ai_evaluation)
                    ai_evaluation_html = _apply_executive_email_styles(_markdown_to_html(ai_evaluation))

                    text_body_message = (
                        f"Nova candidatura recebida\n"
                        f"Nome: {first_name} {last_name}\n"
                        f"Email: {email}\n"
                        f"Telefone: {phone}\n"
                        f"Cidade: {city}\n"
                        f"Estado: {country}\n"
                        f"Experiência (anos): {years_exp}\n"
                        f"Experiência com Securiti ou OneTrust: {privacy_platform_exp}\n"
                        f"Experiência com stack de dados: {tech_stack}\n"
                        f"Disponibilidade para início: {availability}\n"
                        f"Pretensão salarial (USD/mês bruto): {salary_exp}\n"
                        f"Como soube da vaga: {heard_about}\n"
                        f"Informações adicionais: {additional_notes or 'Não informado'}\n"
                        f"Mongo ID: {inserted_id or 'não salvo'}\n\n"
                        f"Avaliação do candidato (OpenAI):\n{ai_evaluation_plain}"
                    )
                    html_body_message = f"""
                    <html>
                        <body>
                            <h2>Nova candidatura recebida</h2>
                            <p><b>Nome:</b> {_to_text(first_name)} {_to_text(last_name)}</p>
                            <p><b>Email:</b> {_to_text(email)}</p>
                            <p><b>Telefone:</b> {_to_text(phone)}</p>
                            <p><b>Cidade:</b> {_to_text(city)}</p>
                            <p><b>Estado:</b> {_to_text(country)}</p>
                            <p><b>Anos de experiência:</b> {_to_text(years_exp)}</p>
                            <p><b>Experiência com Securiti ou OneTrust:</b> {_to_text(privacy_platform_exp)}</p>
                            <p><b>Experiência com stack de dados:</b> {_to_text(tech_stack)}</p>
                            <p><b>Disponibilidade para início:</b> {_to_text(availability)}</p>
                            <p><b>Pretensão salarial (USD/mês bruto):</b> {_to_text(salary_exp)}</p>
                            <p><b>Como você soube desta vaga?:</b> {_to_text(heard_about)}</p>
                            <p><b>Algo mais que você gostaria que soubéssemos?:</b> {_to_text(additional_notes or 'Não informado')}</p>
                            <p><b>ID MongoDB:</b> {_to_text(inserted_id or 'não salvo')}</p>
                            <h3>Avaliação do candidato (OpenAI)</h3>
                            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse; margin-top:8px;">
                                <tr>
                                    <td style="border:1px solid #d0d7de; background-color:#f6f8fa; border-radius:8px; padding:16px; color:#1f2328; font-family:Arial, Helvetica, sans-serif; font-size:14px; line-height:1.5;">
                                        {ai_evaluation_html}
                                    </td>
                                </tr>
                            </table>
                        </body>
                    </html>
                    """

                    recipients = [sender]
                    bcc_recipients = _parse_recipients(destinatarios_bcc)
                    file_path_attach = None

                    try:
                        if resume is not None:
                            _, extension = os.path.splitext(resume.name)
                            with tempfile.NamedTemporaryFile(delete=False, suffix=extension or ".bin") as tmp:
                                tmp.write(resume.getvalue())
                                file_path_attach = tmp.name

                        enviar_html_email(
                            subject=subject,
                            text_body_message=text_body_message,
                            html_body_message=html_body_message,
                            sender=sender,
                            password=password,
                            recipients=recipients,
                            bcc_recipients=bcc_recipients,
                            file_path_attach=file_path_attach,
                        )
                        email_ok = True
                    except Exception as ex:
                        st.error(f"Falha ao enviar e-mail interno: {ex}")
                    finally:
                        if file_path_attach and os.path.exists(file_path_attach):
                            os.remove(file_path_attach)

                    candidate_subject = f"Recebemos sua candidatura | {job_title}"
                    candidate_text_body = (
                        f"Olá, {first_name}!\n\n"
                        "Recebemos sua candidatura com sucesso.\n"
                        "Agradecemos pelo seu interesse na oportunidade e pelo tempo dedicado ao preenchimento do formulário.\n\n"
                        "Nosso time fará a análise do seu perfil e, havendo aderência, entraremos em contato pelos próximos passos.\n\n"
                        "Atenciosamente,\n"
                        "Century Data"
                    )
                    candidate_html_body = f"""
                    <html>
                        <body>
                            <p>Olá, <b>{_to_text(first_name)}</b>!</p>
                            <p>Recebemos sua candidatura com sucesso.</p>
                            <p>
                                Agradecemos pelo seu interesse na oportunidade e pelo tempo dedicado ao preenchimento do formulário.
                            </p>
                            <p>
                                Nosso time fará a análise do seu perfil e, havendo aderência,
                                entraremos em contato pelos próximos passos.
                            </p>
                            <p>Atenciosamente,<br><b>Century Data</b></p>
                        </body>
                    </html>
                    """

                    try:
                        enviar_html_email(
                            subject=candidate_subject,
                            text_body_message=candidate_text_body,
                            html_body_message=candidate_html_body,
                            sender=sender,
                            password=password,
                            recipients=[email],
                            bcc_recipients=[],
                            file_path_attach=None,
                        )
                        candidate_email_ok = True
                    except Exception as ex:
                        st.error(f"Falha ao enviar e-mail ao candidato: {ex}")
                else:
                    st.error("Configuração de e-mail ausente em st.secrets.")

            if mongo_ok and email_ok and candidate_email_ok:
                st.balloons()
                st.success(
                    f"✅ Obrigado(a), **{first_name}**! Sua candidatura foi enviada com sucesso. "
                    "A Century Data analisará seu perfil e retornará em até 5–7 dias úteis."
                )
            elif mongo_ok or email_ok:
                st.warning("⚠️ Submissão finalizada com pendências. Verifique as mensagens acima.")
            else:
                st.error("❌ Submissão finalizada com erro. Verifique as mensagens acima.")