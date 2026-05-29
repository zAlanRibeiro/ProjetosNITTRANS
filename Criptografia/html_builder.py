import base64
import html as html_lib
import json
import os
import sys

try:
    from Criptografia.crypto import ITERACOES, criptografar_dados
except ImportError:
    from crypto import ITERACOES, criptografar_dados


def _carregar_logo() -> str:
    """Retorna o logo NITTRANS como data URL base64, ou string vazia se não encontrado."""
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    caminho = os.path.join(base, 'Logo.png')
    if os.path.isfile(caminho):
        with open(caminho, 'rb') as f:
            return 'data:image/png;base64,' + base64.b64encode(f.read()).decode()
    return ''


# ─── Template HTML — identidade visual NITTRANS ───────────────────────────────
# Placeholders trocados em tempo de execução:
#   __LOGO_SRC__     → data URL base64 do Logo.png
#   __SALT__         → base64 do salt (16 bytes)
#   __IV__           → base64 do IV (12 bytes)
#   __DADOS__        → base64 do ciphertext
#   __NOME_EXIBICAO__ → nome do arquivo (escapado para HTML)
#   __NOME_JSON__    → nome do arquivo (JSON string)
#   __ITERACOES__    → número de iterações PBKDF2

TEMPLATE = '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Documento Criptografado — NITTRANS</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{
  font-family:'Segoe UI',Roboto,Arial,sans-serif;
  background:#EEF2F7;
  color:#1A202C;
  min-height:100vh;
  display:flex;
  flex-direction:column;
}

/* ── Topo ── */
.topbar{
  background:#fff;
  border-bottom:3px solid #1B5299;
  padding:.9rem 1.5rem;
  display:flex;
  align-items:center;
  justify-content:center;
  box-shadow:0 2px 6px rgba(0,0,0,.08);
}
.topbar img{height:52px;object-fit:contain}
.topbar-fallback{
  font-size:1.4rem;font-weight:700;
  color:#1B5299;letter-spacing:.5px;
}
.topbar-fallback span{color:#F5901E}

/* ── Conteúdo principal ── */
main{
  flex:1;
  display:flex;
  justify-content:center;
  align-items:center;
  padding:2rem 1rem;
}

.card{
  background:#fff;
  border-radius:10px;
  box-shadow:0 4px 20px rgba(0,0,0,.10);
  width:100%;
  max-width:460px;
  overflow:hidden;
}

.card-header{
  background:#1B5299;
  padding:1.25rem 1.5rem;
  display:flex;
  align-items:center;
  gap:.85rem;
}
.card-header-icon{font-size:1.5rem}
.card-header-title{font-size:1.05rem;font-weight:600;color:#fff}
.card-header-sub{font-size:.8rem;color:#9BBDE0;margin-top:.15rem}

.card-body{padding:1.5rem}

.filename{
  background:#F4F7FB;
  border:1px solid #DBEAFE;
  border-left:3px solid #1B5299;
  border-radius:6px;
  padding:.65rem .9rem;
  font-size:.85rem;
  color:#374151;
  margin-bottom:1.25rem;
  word-break:break-all;
  display:flex;
  align-items:center;
  gap:.5rem;
}

label{
  display:block;
  font-size:.85rem;
  font-weight:600;
  color:#374151;
  margin-bottom:.4rem;
}

.wrap{position:relative;margin-bottom:1rem}

input{
  width:100%;
  padding:.68rem 2.8rem .68rem .85rem;
  border:1.5px solid #CBD5E0;
  border-radius:6px;
  font-size:.95rem;
  color:#1A202C;
  background:#fff;
  outline:none;
  transition:border-color .15s,box-shadow .15s;
}
input:focus{
  border-color:#1B5299;
  box-shadow:0 0 0 3px rgba(27,82,153,.12);
}

.eye{
  position:absolute;right:.7rem;top:50%;
  transform:translateY(-50%);
  background:none;border:none;
  color:#9CA3AF;cursor:pointer;font-size:1rem;
  padding:0;line-height:1;
}
.eye:hover{color:#1B5299}

.btn{
  width:100%;padding:.75rem;
  background:#F5901E;
  border:none;border-radius:6px;
  color:#fff;font-size:.95rem;font-weight:600;
  cursor:pointer;
  transition:background .2s,transform .1s;
  display:flex;align-items:center;justify-content:center;gap:.5rem;
}
.btn:hover{background:#D97C15}
.btn:active{transform:scale(.99)}
.btn:disabled{background:#CBD5E0;cursor:not-allowed;transform:none}

.btn-sec{
  width:100%;margin-top:.6rem;padding:.55rem;
  background:none;
  border:1.5px solid #CBD5E0;
  border-radius:6px;
  color:#9CA3AF;font-size:.82rem;cursor:pointer;
  transition:all .2s;
}
.btn-sec:hover{border-color:#F5901E;color:#F5901E}

#st{margin-top:1rem;font-size:.88rem;text-align:center;min-height:1.4em}
.ok{color:#059669;font-weight:600}
.err{color:#DC2626;font-weight:600}
.spin{color:#6B7280}

.dbg{
  margin-top:1rem;padding:.75rem;
  background:#F8FAFC;
  border:1px solid #E2E8F0;
  border-radius:6px;
  font-size:.72rem;color:#9CA3AF;
  line-height:1.8;word-break:break-all;
}
.dbg span{color:#4A5568;font-weight:600}

/* ── Rodapé ── */
footer{
  text-align:center;
  padding:.85rem 1rem;
  font-size:.78rem;
  color:#9CA3AF;
  border-top:1px solid #E2E8F0;
  background:#fff;
}
footer strong{color:#1B5299}
footer a{color:#F5901E;text-decoration:none}
footer a:hover{text-decoration:underline}
</style>
</head>
<body>

<div class="topbar">
  <img src="__LOGO_SRC__" alt="NITTRANS"
       onerror="this.style.display='none';document.getElementById('logo-fb').style.display='block'">
  <div id="logo-fb" class="topbar-fallback" style="display:none">
    Nit<span>trans</span>
  </div>
</div>

<main>
<div class="card">
  <div class="card-header">
    <div>
      <div class="card-header-title">Documento Criptografado</div>
      <div class="card-header-sub">Insira a senha para acessar o arquivo</div>
    </div>
  </div>

  <div class="card-body">
    <div class="filename">
      📄 __NOME_EXIBICAO__
    </div>

    <label for="s">Senha de acesso</label>
    <div class="wrap">
      <input type="password" id="s" placeholder="Digite a senha..."
             autocomplete="current-password"
             onkeydown="if(event.key==='Enter')dec()">
      <button class="eye"
              onclick="var e=document.getElementById('s');e.type=e.type==='password'?'text':'password'"
              title="Mostrar/ocultar">👁</button>
    </div>

    <button class="btn" id="b" onclick="dec()">
       Descriptografar e Baixar
    </button>

    <button class="btn-sec" onclick="dlEnc()">
       Baixar dados criptografados (.bin)
    </button>

    <p id="st"></p>

    <div class="dbg" id="dbg" style="display:none">
      <div><span>Salt&nbsp;&nbsp;(16 B):</span> __SALT__</div>
      <div><span>IV&nbsp;&nbsp;&nbsp;(12 B):</span> __IV__</div>
      <div><span>Cipher&nbsp;&nbsp;&nbsp;&nbsp;:</span> AES-256-GCM</div>
      <div><span>KDF&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;:</span> PBKDF2-SHA256 (__ITERACOES__ iter.)</div>
    </div>
  </div>
</div>
</main>

<footer>
  <strong>NITTRANS</strong> — Niterói Transporte e Trânsito &nbsp;|&nbsp;
  Prefeitura Municipal de Niterói
</footer>

<script>
const D={salt:"__SALT__",iv:"__IV__",d:"__DADOS__",n:__NOME_JSON__};
const MAX_TENTATIVAS=10;
const STORE_KEY='lk_'+D.salt.slice(0,12);
let tentativas=0,bloqueadoAte=0;

function b(s){return Uint8Array.from(atob(s),c=>c.charCodeAt(0));}

function salvar(){
  try{localStorage.setItem(STORE_KEY,JSON.stringify({t:tentativas,b:bloqueadoAte}));}catch{}
}
function carregar(){
  try{
    const s=JSON.parse(localStorage.getItem(STORE_KEY)||'{}');
    tentativas=s.t||0;bloqueadoAte=s.b||0;
  }catch{}
}

function delayMs(n){return Math.min(2000*Math.pow(2,n-1),600000);}

async function contagem(ms){
  const st=document.getElementById('st'),btn=document.getElementById('b');
  btn.disabled=true;
  const fim=Date.now()+ms;
  while(Date.now()<fim){
    const s=Math.ceil((fim-Date.now())/1000);
    const m=Math.floor(s/60),seg=s%60;
    const t=m>0?`${m}min ${seg}s`:`${s}s`;
    st.innerHTML=`<span class="err"> Aguarde ${t} para tentar novamente. (${tentativas}/${MAX_TENTATIVAS})</span>`;
    await new Promise(r=>setTimeout(r,500));
  }
  btn.disabled=false;
}

function dlEnc(){
  const a=Object.assign(document.createElement('a'),
    {href:URL.createObjectURL(new Blob([b(D.d)])),download:D.n+'.bin'});
  a.click();
  document.getElementById('dbg').style.display='block';
}

async function dec(){
  const st=document.getElementById('st'),btn=document.getElementById('b');
  if(tentativas>=MAX_TENTATIVAS){
    st.innerHTML='<span class="err"> Número máximo de tentativas atingido.</span>';
    btn.disabled=true;return;
  }
  const agora=Date.now();
  if(agora<bloqueadoAte){
    const s=Math.ceil((bloqueadoAte-agora)/1000);
    st.innerHTML=`<span class="err"> Aguarde ${s}s antes de tentar novamente.</span>`;
    return;
  }
  const pw=document.getElementById('s').value;
  if(!pw){st.innerHTML='<span class="err">Digite a senha.</span>';return;}
  btn.disabled=true;
  st.innerHTML='<span class="spin"> Descriptografando, aguarde...</span>';
  try{
    const km=await crypto.subtle.importKey('raw',new TextEncoder().encode(pw),'PBKDF2',false,['deriveKey']);
    const k=await crypto.subtle.deriveKey(
      {name:'PBKDF2',salt:b(D.salt),iterations:__ITERACOES__,hash:'SHA-256'},
      km,{name:'AES-GCM',length:256},false,['decrypt']);
    const dec=await crypto.subtle.decrypt({name:'AES-GCM',iv:b(D.iv)},k,b(D.d));
    const a=Object.assign(document.createElement('a'),
      {href:URL.createObjectURL(new Blob([dec])),download:D.n});
    a.click();
    tentativas=0;bloqueadoAte=0;salvar();
    st.innerHTML='<span class="ok">✔ Arquivo baixado com sucesso!</span>';
    btn.disabled=false;
  }catch{
    tentativas++;salvar();
    if(tentativas>=MAX_TENTATIVAS){
      st.innerHTML='<span class="err"> Número máximo de tentativas atingido.</span>';
      return;
    }
    const ms=delayMs(tentativas);
    bloqueadoAte=Date.now()+ms;salvar();
    await contagem(ms);
  }
}

carregar();
if(tentativas>=MAX_TENTATIVAS){
  document.getElementById('b').disabled=true;
  document.getElementById('st').innerHTML='<span class="err">🚫 Número máximo de tentativas atingido.</span>';
}else if(bloqueadoAte>Date.now()){
  contagem(bloqueadoAte-Date.now());
}
document.getElementById('s').addEventListener('keydown',e=>{if(e.key==='Enter')dec();});
</script>
</body>
</html>'''


def gerar_html(caminho: str, senha: str, destino: str | None = None) -> str:
    """Criptografa o arquivo e gera um HTML autocontido com identidade NITTRANS.

    Se `destino` não for informado, salva ao lado do arquivo original.
    """
    salt, iv, ciphertext = criptografar_dados(caminho, senha)
    nome = os.path.basename(caminho)

    conteudo = (TEMPLATE
                .replace("__LOGO_SRC__", _carregar_logo())
                .replace("__SALT__", base64.b64encode(salt).decode())
                .replace("__IV__", base64.b64encode(iv).decode())
                .replace("__DADOS__", base64.b64encode(ciphertext).decode())
                .replace("__NOME_EXIBICAO__", html_lib.escape(nome))
                .replace("__NOME_JSON__", json.dumps(nome))
                .replace("__ITERACOES__", str(ITERACOES)))

    if destino is None:
        destino = caminho + ".html"

    with open(destino, "w", encoding="utf-8") as f:
        f.write(conteudo)

    return destino
