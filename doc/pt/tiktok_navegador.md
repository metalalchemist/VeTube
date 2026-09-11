# Ler o TikTok pelo navegador: a extensão do assinador local

Este guia explica uma forma alternativa de ler o chat de uma live do TikTok no VeTube, pensada para quando o método habitual falha. Ele foi pensado para ser lido do início ao fim: primeiro para que serve, depois por que existe, como instalar e usar, e por fim as notas de segurança.

## Para que serve

Para ler o chat de uma live, o TikTok exige que a requisição ao *websocket* do chat venha **assinada**. O VeTube normalmente pede essa assinatura a um serviço externo (EulerStream). Quando esse serviço cai — o que acontece com frequência — o VeTube não consegue ler o chat de **nenhuma** live do TikTok pela via habitual.

A extensão resolve exatamente isso: em vez de depender desse serviço externo, ela deixa que o **seu próprio navegador** — que já tem a live aberta e já está recebendo o chat por uma conexão assinada e funcionando — passe essas mensagens ao VeTube. A extensão não calcula nenhuma assinatura nova: apenas copia as mensagens que o seu navegador já está recebendo.

Em uma frase: *o VeTube lê por cima do ombro do seu navegador, que é quem realmente está conectado ao TikTok.*

## Por que ela foi criada

Não existe uma API oficial para ler o chat de uma live do TikTok, então o VeTube (e qualquer programa parecido) depende de um serviço externo para calcular a assinatura que o TikTok exige. Esse serviço, o EulerStream:

- cai com frequência (e enquanto está fora do ar, ninguém consegue ler nenhuma live do TikTok por essa via),
- reparte uma cota limitada entre todos os seus usuários,
- é um terceiro externo ao VeTube.

Como não é possível evitar a assinatura, a extensão foi criada para resolver isso sem depender desse terceiro: se o seu navegador já está vendo a live com uma conexão assinada e funcionando, não é preciso pedir a assinatura a mais ninguém. É uma alternativa, não um substituto definitivo: serve para quando o serviço habitual falha.

## Como instalar

A extensão **não está na Chrome Web Store**: ela vem incluída com o VeTube, na pasta `interceptor_extension`. Para instalá-la, uma única vez:

1. Abra o Chrome (ou um navegador baseado em Chromium, como Edge ou Brave) e acesse `chrome://extensions`.
2. Ative o **"Modo do desenvolvedor"** (interruptor no canto superior direito).
3. Clique em **"Carregar sem compactação"** e escolha a pasta `interceptor_extension` (que vem junto com o VeTube).
4. Pronto: aparece **"VeTube – ponte do chat do TikTok Live"** na lista de extensões.

## Como usar

Na tela inicial do VeTube, no menu suspenso **"Capturar o chat de:"**, há duas opções para o TikTok: **"TikTok"** (o serviço habitual) e **"TikTok (navegador, experimental)"** (esta extensão). Para usar a extensão diretamente:

1. Abra a live no seu navegador (com a extensão já instalada). O Chrome vai mostrar uma barra dizendo *"... está depurando este navegador"*: isso é normal e é o sinal de que a extensão está lendo o chat. Não a feche.
2. No VeTube, digite o **mesmo usuário** da live (o `@usuario`, exatamente como aparece).
3. Escolha **"TikTok (navegador, experimental)"** em "Capturar o chat de:" e clique em **Acessar**.

Você também pode deixar o VeTube oferecer isso automaticamente: se escolher o "TikTok" normal e a conexão habitual falhar, o VeTube vai perguntar se você quer passar a ler pelo navegador (com a live já aberta lá). Se aceitar, ele continua lendo sem reiniciar nada.

Requisitos: a extensão precisa estar carregada **antes** de abrir a live (se a aba já estava aberta, recarregue-a), e as ferramentas do desenvolvedor (F12) não podem estar abertas nessa aba, pois usam o mesmo canal da extensão.

## Notas de segurança

- **A extensão apenas lê o que o seu navegador já recebe.** Ela não burla nenhuma proteção do TikTok: a assinatura continua sendo feita pelo TikTok, na sua própria sessão, como sempre.
- **Ela nunca envia o seu cookie de sessão** (`sessionid`) nem nenhuma credencial da sua conta. O chat de uma live pública funciona da mesma forma sem estar logado.
- **Tudo fica no seu computador.** A extensão só fala com `127.0.0.1:8790` (o VeTube, na sua própria máquina); nada é enviado a nenhum servidor externo ou terceiro.
- **Ela não modifica a página do TikTok** nem interfere na sua segurança: apenas observa o tráfego do chat, da mesma forma que as ferramentas do desenvolvedor do navegador veriam.

Mais detalhes técnicos (como a extensão é feita, o protocolo que ela usa para falar com o VeTube, e diagnóstico caso algo não funcione) estão em `FIRMADOR_LOCAL.md` e `interceptor_extension/LEEME.md`, no código-fonte do VeTube.
