"""
Validadores y utilidades para extracción de features laborales.

Contiene 120+ keywords de skills técnicas, funciones de extracción
de experiencia, detección de cargo/modalidad/categoría de rol,
y utilidades de seguridad (masking de tokens, hash de archivos).

Author: Lilliana Uribe González
Version: 2.0
"""

import re  # Expresiones regulares para patrones de búsqueda
from typing import Optional  # Type hints para optionales

SKILL_KEYWORDS = {  # Diccionario de 120+ skills técnicas con sus patrones regex
    "Python": r"(?i)\bpython\b",  # Detecta "python" sin importar mayúsculas
    "Java": r"(?i)\bjava\b",  # Detecta "java"
    "JavaScript": r"(?i)\b(?:javascript|js)\b",  # Detecta "javascript" o "js"
    "TypeScript": r"(?i)\btypescript\b",  # Detecta "typescript"
    "SQL": r"(?i)\bsql\b",  # Detecta "sql"
    "AWS": r"(?i)\baws\b",  # Detecta "aws"
    "Azure": r"(?i)\bazure\b",  # Detecta "azure"
    "GCP": r"(?i)\bgcp\b|google cloud",  # Detecta "gcp" o "google cloud"
    "Docker": r"(?i)\bdocker\b",  # Detecta "docker"
    "Kubernetes": r"(?i)\bkubernetes|k8s\b",  # Detecta "kubernetes" o "k8s"
    "React": r"(?i)\breact\b",  # Detecta "react"
    "Angular": r"(?i)\bangular\b",  # Detecta "angular"
    "Vue": r"(?i)\bvue\.?js\b",  # Detecta "vuejs" o "vue.js"
    "Node.js": r"(?i)\bnode\.?js\b",  # Detecta "nodejs" o "node.js"
    "Django": r"(?i)\bdjango\b",  # Detecta "django"
    "Flask": r"(?i)\bflask\b",  # Detecta "flask"
    "Spring Boot": r"(?i)\bspring boot\b",  # Detecta "spring boot"
    ".NET": r"(?i)\.net\b|dotnet",  # Detecta ".net" o "dotnet"
    "PHP": r"(?i)\bphp\b",  # Detecta "php"
    "Ruby": r"(?i)\bruby\b",  # Detecta "ruby"
    "Go": r"(?i)\bgo\b|golang",  # Detecta "go" o "golang"
    "Rust": r"(?i)\brust\b",  # Detecta "rust"
    "C++": r"(?i)\bc\+\+\b",  # Detecta "c++"
    "C#": r"(?i)\bc#\b",  # Detecta "c#"
    "Swift": r"(?i)\bswift\b",  # Detecta "swift"
    "Kotlin": r"(?i)\bkotlin\b",  # Detecta "kotlin"
    "Dart": r"(?i)\bdart\b",  # Detecta "dart"
    "Flutter": r"(?i)\bflutter\b",  # Detecta "flutter"
    "React Native": r"(?i)\breact native\b",  # Detecta "react native"
    "Git": r"(?i)\bgit\b",  # Detecta "git"
    "Linux": r"(?i)\blinux\b",  # Detecta "linux"
    "CI/CD": r"(?i)\bci/cd\b|continuous integration",  # Detecta "ci/cd" o "continuous integration"
    "Agile": r"(?i)\bagile\b|scrum",  # Detecta "agile" o "scrum"
    "MySQL": r"(?i)\bmysql\b",  # Detecta "mysql"
    "PostgreSQL": r"(?i)\bpostgresql|postgres\b",  # Detecta "postgresql" o "postgres"
    "MongoDB": r"(?i)\bmongodb\b",  # Detecta "mongodb"
    "Redis": r"(?i)\bredis\b",  # Detecta "redis"
    "GraphQL": r"(?i)\bgraphql\b",  # Detecta "graphql"
    "REST API": r"(?i)\brest\b|api",  # Detecta "rest" o "api"
    "HTML/CSS": r"(?i)\bhtml\b|\bcss\b",  # Detecta "html" o "css"
    "Next.js": r"(?i)\bnext\.?js\b",  # Detecta "nextjs" o "next.js"
    "Nuxt.js": r"(?i)\bnuxt\.?js\b",  # Detecta "nuxtjs" o "nuxt.js"
    "Svelte": r"(?i)\bsvelte\b",  # Detecta "svelte"
    "Express.js": r"(?i)\bexpress\.?js\b",  # Detecta "expressjs" o "express.js"
    "FastAPI": r"(?i)\bfastapi\b",  # Detecta "fastapi"
    "Tailwind CSS": r"(?i)\btailwind\b",  # Detecta "tailwind"
    "Bootstrap": r"(?i)\bbootstrap\b",  # Detecta "bootstrap"
    "Machine Learning": r"(?i)\bmachine learning\b|ml\b",  # Detecta "machine learning" o "ml"
    "Data Science": r"(?i)\bdata science\b|científico de datos\b",  # Detecta "data science" o "científico de datos"
    "TensorFlow": r"(?i)\btensorflow\b",  # Detecta "tensorflow"
    "PyTorch": r"(?i)\bpytorch\b",  # Detecta "pytorch"
    "Deep Learning": r"(?i)\bdeep learning\b|red neuronal|neural network",  # Detecta "deep learning" o "red neuronal"
    "NLP": r"(?i)\bnlp\b|natural language|procesamiento lenguaje",  # Detecta "nlp" o "natural language"
    "Computer Vision": r"(?i)\bcomputer vision\b|visión artificial|visión por computador",  # Detecta "computer vision" o "visión artificial"
    "LLM": r"(?i)\bllm\b|lenguaje natural|largo alcance|lenguaje de máquina",  # Detecta "llm"
    "LangChain": r"(?i)\blangchain\b",  # Detecta "langchain"
    "Hugging Face": r"(?i)\bhugging\s*face\b|huggingface",  # Detecta "hugging face" o "huggingface"
    "OpenAI": r"(?i)\bopenai\b|gpt-?4|gpt-?3",  # Detecta "openai", "gpt-4" o "gpt-3"
    "Generative AI": r"(?i)\bgenerative\s*ai\b|gen\s*ai|ia generativa|generativa",  # Detecta "generative ai" o "ia generativa"
    "Prompt Engineering": r"(?i)\bprompt\b|ingeniería de prompts",  # Detecta "prompt" o "ingeniería de prompts"
    "RAG": r"(?i)\brag\b|retrieval augmented",  # Detecta "rag" o "retrieval augmented"
    "Vector DB": r"(?i)\bvector\s*(database|db|base)\b|chromadb|pinecone|weaviate",  # Detecta bases de datos vectoriales
    "Transformers": r"(?i)\btransformers\b|bert|roberta",  # Detecta "transformers", "bert" o "roberta"
    "Reinforcement Learning": r"(?i)\breinforcement learning\b|rl\b",  # Detecta "reinforcement learning" o "rl"
    "GANs": r"(?i)\bgans?\b|generative adversarial",  # Detecta "gans" o "generative adversarial"
    "Pandas": r"(?i)\bpandas\b",  # Detecta "pandas"
    "NumPy": r"(?i)\bnumpy\b|numpy",  # Detecta "numpy"
    "Scikit-learn": r"(?i)\bscikit\b|sklearn",  # Detecta "scikit" o "sklearn"
    "Matplotlib": r"(?i)\bmatplotlib\b",  # Detecta "matplotlib"
    "Seaborn": r"(?i)\bseaborn\b",  # Detecta "seaborn"
    "Power BI": r"(?i)\bpower\s*bi\b",  # Detecta "power bi"
    "Tableau": r"(?i)\btableau\b",  # Detecta "tableau"
    "Looker": r"(?i)\blooker\b",  # Detecta "looker"
    "Airflow": r"(?i)\bairflow\b",  # Detecta "airflow"
    "Spark": r"(?i)\bspark\b|pyspark",  # Detecta "spark" o "pyspark"
    "Hadoop": r"(?i)\bhadoop\b",  # Detecta "hadoop"
    "Hive": r"(?i)\bhive\b",  # Detecta "hive"
    "Snowflake": r"(?i)\bsnowflake\b",  # Detecta "snowflake"
    "DBT": r"(?i)\bdbt\b",  # Detecta "dbt"
    "Big Data": r"(?i)\bbig\s*data\b|datos masivos",  # Detecta "big data" o "datos masivos"
    "Data Analytics": r"(?i)\bdata\s*analytics\b|analítica de datos",  # Detecta "data analytics" o "analítica de datos"
    "ETL": r"(?i)\betl\b",  # Detecta "etl"
    "Apache Kafka": r"(?i)\bkafka\b",  # Detecta "kafka"
    "Databricks": r"(?i)\bdatabricks\b",  # Detecta "databricks"
    "Terraform": r"(?i)\bterraform\b",  # Detecta "terraform"
    "Ansible": r"(?i)\bansible\b",  # Detecta "ansible"
    "Jenkins": r"(?i)\bjenkins\b",  # Detecta "jenkins"
    "GitLab CI": r"(?i)\bgitlab ci\b",  # Detecta "gitlab ci"
    "GitHub Actions": r"(?i)\bgithub actions\b",  # Detecta "github actions"
    "Prometheus": r"(?i)\bprometheus\b",  # Detecta "prometheus"
    "Grafana": r"(?i)\bgrafana\b",  # Detecta "grafana"
    "ELK Stack": r"(?i)\belk\b|elasticsearch|logstash|kibana",  # Detecta "elk", "elasticsearch", "logstash" o "kibana"
    "Microservices": r"(?i)\bmicroservices?\b|microservicios",  # Detecta "microservices" o "microservicios"
    "ROS": r"(?i)\bros\b|robot operating system",  # Detecta "ros" o "robot operating system"
    "PLC": r"(?i)\bplc\b|controlador lógico",  # Detecta "plc" o "controlador lógico"
    "SCADA": r"(?i)\bscada\b",  # Detecta "scada"
    "Arduino": r"(?i)\barduino\b",  # Detecta "arduino"
    "Raspberry Pi": r"(?i)\b(?:raspberry\s*pi|raspberry)\b",  # Detecta "raspberry pi" o "raspberry"
    "Ciberseguridad": r"(?i)\bciberseguridad\b|cybersecurity|seguridad informática",  # Detecta "ciberseguridad" o "cybersecurity"
    "Ethical Hacking": r"(?i)\bhacking\s*ético\b|ethical hacking|pentest",  # Detecta "hacking ético" o "ethical hacking"
    "SIEM": r"(?i)\bsiem\b|splunk|qradar",  # Detecta "siem", "splunk" o "qradar"
    "Kali Linux": r"(?i)\bkali\s*linux\b",  # Detecta "kali linux"
    "Wireshark": r"(?i)\bwireshark\b",  # Detecta "wireshark"
    "Firewalls": r"(?i)\bfirewall\b",  # Detecta "firewall"
    "Unity": r"(?i)\bunity\b",  # Detecta "unity"
    "Unreal Engine": r"(?i)\bunreal\s*engine\b",  # Detecta "unreal engine"
    "Blender": r"(?i)\bblender\b",  # Detecta "blender"
    "Web3": r"(?i)\bweb3\b",  # Detecta "web3"
    "Solidity": r"(?i)\bsolidity\b",  # Detecta "solidity"
    "Blockchain": r"(?i)\bblockchain\b",  # Detecta "blockchain"
    "IoT": r"(?i)\biot\b|internet of things|internet de las cosas",  # Detecta "iot" o "internet of things"
    "AR/VR": r"(?i)\brealidad virtual\b|realidad aumentada|virtual reality|augmented reality",  # Detecta realidad virtual/aumentada
    "Quantum Computing": r"(?i)\bcomputación cuántica\b|quantum computing",  # Detecta computación cuántica
    "Mechatronics": r"(?i)\bmecatrónica\b|mecatronica|mechatronics",  # Detecta mecatrónica
    "Automatización": r"(?i)\bautomatización\b|automatizacion|automation",  # Detecta automatización
}

ROLE_CATEGORIES = {  # Categorías de roles con patrones regex para identificación
    "Desarrollo de Software": [  # Patrones para detectar roles de desarrollo
        r"(?i)\bdesarrollador\b",  # "desarrollador"
        r"(?i)\bdeveloper\b",  # "developer"
        r"(?i)\bprogramador\b",  # "programador"
        r"(?i)\bprogrammer\b",  # "programmer"
        r"(?i)\bingeniero de software\b",  # "ingeniero de software"
        r"(?i)\bsoftware engineer\b",  # "software engineer"
        r"(?i)\bdesarrollo web\b",  # "desarrollo web"
        r"(?i)\bweb developer\b",  # "web developer"
        r"(?i)\bdesarrollo móvil\b|mobile developer",  # "desarrollo móvil"
        r"(?i)\bfull.?stack\b",  # "fullstack" o "full-stack"
        r"(?i)\bfront.?end\b",  # "frontend" o "front-end"
        r"(?i)\bback.?end\b",  # "backend" o "back-end"
    ],
    "Analítica de Datos": [  # Patrones para detectar roles de analítica
        r"(?i)\banalista de datos\b",  # "analista de datos"
        r"(?i)\bdata analyst\b",  # "data analyst"
        r"(?i)\banalítica\b",  # "analítica"
        r"(?i)\banalytics\b",  # "analytics"
        r"(?i)\bbi\b|business intelligence",  # "bi" o "business intelligence"
    ],
    "Ciencia de Datos": [  # Patrones para detectar roles de ciencia de datos
        r"(?i)\bdata science\b",  # "data science"
        r"(?i)\bcientífico de datos\b",  # "científico de datos"
        r"(?i)\bdata scientist\b",  # "data scientist"
    ],
    "Ingeniería de Datos": [  # Patrones para detectar roles de ingeniería de datos
        r"(?i)\bdata engineer\b",  # "data engineer"
        r"(?i)\bingeniero de datos\b",  # "ingeniero de datos"
        r"(?i)\bbig data\b",  # "big data"
        r"(?i)\bdata engineering\b",  # "data engineering"
        r"(?i)\bdata pipeline\b",  # "data pipeline"
        r"(?i)\betl\b",  # "etl"
    ],
    "Inteligencia Artificial": [  # Patrones para detectar roles de IA
        r"(?i)\binteligencia artificial\b",  # "inteligencia artificial"
        r"(?i)\bai\b|artificial intelligence",  # "ai" o "artificial intelligence"
        r"(?i)\bing.?\s*(?:en\s*)?ia\b",  # "ing en ia" o "ing. ia"
    ],
    "Machine Learning": [  # Patrones para detectar roles de ML
        r"(?i)\bmachine learning\b",  # "machine learning"
        r"(?i)\bml\s*(?:engineer|engineer)\b",  # "ml engineer"
    ],
    "Deep Learning": [  # Patrones para detectar roles de deep learning
        r"(?i)\bdeep learning\b",  # "deep learning"
        r"(?i)\bred neuronal\b|neural network",  # "red neuronal"
        r"(?i)\bnlp\b|natural language",  # "nlp" o "natural language"
        r"(?i)\bcomputer vision\b|visión artificial",  # "computer vision"
    ],
}


def identify_role_category(title: str, desc: str = "") -> str:
    """Identifica la categoría de rol desde título y descripción."""
    text = f"{title} {desc}".lower()  # Combina título y descripción en minúsculas
    for role, patterns in ROLE_CATEGORIES.items():  # Itera cada categoría
        for p in patterns:  # Itera cada patrón de la categoría
            if re.search(p, text):  # Si el patrón coincide con el texto
                return role  # Retorna la categoría encontrada
    return "Otros"  # Si ningún patrón coincide, retorna "Otros"


def extract_experience_years(text: str) -> Optional[float]:
    """Extrae años de experiencia desde texto con múltiples patrones regex."""
    if not text or not isinstance(text, str):  # Si no hay texto o no es string
        return None  # Retorna None
    patterns = [  # Lista de patrones regex con grupo a extraer
        (r"(?i)(\d+)\s*(?:años?|anos?|a|years?)\s*(?:de\s*)?(?:experiencia|exp)", 1),  # "3 años de experiencia" → 3
        (r"(?i)(\d+)\s*[+-]\s*(?:años?|anos?|a)", 1),  # "3+ años" → 3
        (r"(?i)entre\s*(\d+)\s*y\s*(\d+)", 2),  # "entre 3 y 5" → promedio
        (r"(?i)más\s*de\s*(\d+)", 1),  # "más de 5" → 5
        (r"(?i)(\d+)\s*[_-]\s*(\d+)", 2),  # "3-5" o "3_5" → promedio
        (r"(?i)sin\s*experiencia", 0),  # "sin experiencia" → 0
        (r"(?i)reciente\s*graduad", 0),  # "reciente graduado" → 0
        (r"(?i)no\s*requiere\s*experiencia", 0),  # "no requiere experiencia" → 0
    ]
    for pattern, group in patterns:  # Itera cada patrón
        m = re.search(pattern, text)  # Busca el patrón en el texto
        if m:  # Si encontró coincidencia
            if group == 2:  # Si necesita promediar 2 grupos
                return (float(m.group(1)) + float(m.group(2))) / 2  # Promedio de los 2 números
            if group == 0:  # Si es caso especial (sin experiencia)
                return 0.0  # Retorna 0
            return float(m.group(1))  # Retorna el número encontrado
    match = re.search(r"(?i)(\d+)\s*(?:años?|anos?)", text)  # Patrón genérico: "N años"
    if match:  # Si encontró
        return float(match.group(1))  # Retorna el número
    return None  # Si no encontró ningún patrón


def extract_skills(text: str) -> list:
    """Extrae skills técnicas del texto usando los 120+ patrones regex."""
    if not text or not isinstance(text, str):  # Si no hay texto o no es string
        return []  # Retorna lista vacía
    found = []  # Lista de skills encontradas
    for skill, pattern in SKILL_KEYWORDS.items():  # Itera cada skill y su patrón
        if re.search(pattern, text):  # Si el patrón coincide con el texto
            found.append(skill)  # Agrega la skill a la lista
    return found  # Retorna lista de skills encontradas


def identify_cargo_level(title: str) -> str:
    """Identifica el nivel del cargo desde el título."""
    if not title or not isinstance(title, str):  # Si no hay título o no es string
        return "ingeniero"  # Default: ingeniero
    t = title.lower()  # Convierte a minúsculas
    if any(k in t for k in ["senior", "sr.", "sr ", "lead", "principal", "arquitecto", "architect", "manager", "director", "jefe", "head of"]):  # Si contiene palabras de nivel senior
        return "senior"  # Retorna senior
    if any(k in t for k in ["técnico", "tecnico", "technician", "soporte", "help desk", "mesa de ayuda"]):  # Si contiene palabras de técnico
        return "tecnico"  # Retorna técnico
    if any(k in t for k in ["tecnólogo", "tecnologo", "technologist", "analista programador"]):  # Si contiene palabras de tecnólogo
        return "tecnologo"  # Retorna tecnólogo
    if any(k in t for k in [  # Si contiene palabras de ingeniero
        "ingeniero", "engineer", "ing.",
        "desarrollador", "developer", "programador", "programmer",
        "analista", "analyst",
        "data scientist", "cientifico de datos",
        "machine learning", "inteligencia artificial", "ia",
        "prompt", "chatbot",
        "data engineer", "big data",
        "fullstack", "full-stack", "full_stack",
        "back-end", "backend", "back end",
        "front-end", "frontend", "front end",
        "devops", "devops",
        "consultor", "consultant",
        "especialista", "specialist",
        "investigador", "researcher",
        "bi", "business intelligence",
        "automatización", "automation",
        "quality assurance", "qa", "tester",
        "solutions architect",
    ]):
        return "ingeniero"  # Retorna ingeniero
    return "ingeniero"  # Default: ingeniero


def identify_modalidad(text: str) -> str:
    """Identifica la modalidad de trabajo desde texto."""
    if not text or not isinstance(text, str):  # Si no hay texto o no es string
        return "presencial"  # Default: presencial
    t = text.lower()  # Convierte a minúsculas
    if any(k in t for k in ["remoto", "remote", "virtual", "teletrabajo"]):  # Si contiene palabras de remoto
        return "remoto"  # Retorna remoto
    if any(k in t for k in ["híbrid", "hibrid", "hybrid", "mixto"]):  # Si contiene palabras de híbrido
        return "hibrido"  # Retorna híbrido
    return "presencial"  # Default: presencial


SALARY_RANGES = {  # Rangos salariales por nivel de cargo (COP mensuales)
    "tecnico": (1_000_000, 4_000_000),  # Técnico: $1M - $4M
    "tecnologo": (1_500_000, 5_000_000),  # Tecnólogo: $1.5M - $5M
    "ingeniero": (2_000_000, 8_000_000),  # Ingeniero: $2M - $8M
    "senior": (4_000_000, 15_000_000),  # Senior: $4M - $15M
}


def validate_salary_range(salary: float, level: str = "ingeniero") -> bool:
    """Valida si un salario está dentro del rango esperado para el nivel."""
    min_sal, max_sal = SALARY_RANGES.get(level, (1_000_000, 30_000_000))  # Obtiene rango del nivel
    return min_sal * 0.5 <= salary <= max_sal * 3  # Permite ±50% del mínimo y 3x el máximo


def sanitize_user_input(value: str) -> str:
    """Limpia y sanitiza input del usuario."""
    if not isinstance(value, str):  # Si no es string
        return str(value) if value else ""  # Convierte a string o retorna vacío
    return value.strip()[:200]  # Limpia espacios y limita a 200 caracteres
