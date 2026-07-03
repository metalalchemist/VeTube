# VeTube e Discord: guia passo a passo

O VeTube pode ler em tempo real as mensagens de um canal de texto de um servidor do Discord. Para fazer isso pela via oficial, o Discord exige o uso de um «bot»: uma conta especial que você mesmo cria de graça, uma única vez, em cerca de 10 minutos. Este guia explica todo o processo e foi pensado para usuários de leitores de tela (sem capturas de tela, com os nomes exatos de cada botão).

Observação: o portal de desenvolvedores do Discord é exibido no idioma da sua conta do Discord quando disponível; caso contrário, em inglês. Os nomes dos botões abaixo são dados em inglês como referência; se o seu portal estiver traduzido, eles aparecerão no seu idioma.

## O que você precisa
- Uma conta do Discord.
- Permissão para convidar bots para o servidor que você quer ler (permissão «Gerenciar servidor»). Se você não a tiver, no final do passo 4 poderá enviar o link de convite para um administrador abrir por você.

## Passo 1: criar o aplicativo
1. Abra https://discord.com/developers/applications e faça login.
2. Pressione o botão «New Application».
3. Digite um nome (por exemplo «VeTube»), aceite os termos e pressione «Create».

## Passo 2: obter o token do bot
1. Na página do seu aplicativo, vá até a seção «Bot» no menu à esquerda.
2. Pressione o botão «Reset Token» e confirme com «Yes, do it!».
3. O Discord pede novamente a sua senha (ou a sua chave de acesso) para confirmar que é você: digite-a e confirme. Se você tiver verificação em duas etapas, o código também pode ser solicitado.
4. O novo token aparece com um botão «Copy» para copiá-lo para a área de transferência. Cole-o temporariamente em um lugar seguro, por exemplo o Bloco de Notas: por segurança, o token só é mostrado uma vez, na criação.

Importante: o token é como a senha do seu bot. Não o compartilhe nem o publique. Se ele vazar, volte a esta página e pressione «Reset Token» para gerar outro; o anterior deixa de funcionar.

## Passo 3: ativar o «Message Content Intent»
Sem esta opção, o Discord não permite que o bot leia o conteúdo das mensagens.
1. Ainda na seção «Bot», desça até «Privileged Gateway Intents».
2. Ative o interruptor «Message Content Intent».
3. Pressione «Save Changes» na barra que aparece.

## Passo 4: convidar o bot para o seu servidor
1. Vá até a seção «OAuth2» no menu à esquerda e localize o «URL Generator».
2. Na lista «Scopes», marque a caixa «bot».
3. Em «Bot Permissions», que aparece abaixo, marque «View Channels» e «Read Message History».
4. No final da página, em «Generated URL», pressione «Copy».
5. Abra essa URL no navegador e escolha o seu servidor na caixa combinada «Adicionar ao servidor». Dica com leitor de tela: enquanto nenhum servidor estiver escolhido, o botão de baixo se chama «Você não preencheu alguns campos»; depois de escolher o servidor ele passa a se chamar «Autorizar». Pressione-o. (Se você não puder convidar bots, envie essa URL para um administrador do servidor.)

## Passo 5: copiar o link do canal
1. No Discord, localize o canal de texto que você quer ler.
2. Abra o menu de contexto do canal: clique com o botão direito, ou tecla de aplicações ou Shift+F10 com o leitor de tela.
3. Escolha «Copiar link». O link tem esta forma: https://discord.com/channels/1234567890/0987654321

## Passo 6: colar no VeTube
1. Abra o VeTube, cole o link do canal na caixa de texto principal e pressione «Acessar» ou Enter.
2. Na primeira vez, o VeTube pedirá o token do bot: cole-o e pressione «Aceitar». Ele ficará salvo e não será pedido novamente.
3. Pronto! As mensagens do canal começam a chegar. As mensagens do dono do servidor e de quem pode moderar aparecem na categoria «Moderadores»; o resto vai para «Geral».

## Solução de problemas
- «O token não é válido»: copie o token completo do portal (passo 2). Na dúvida, gere um novo com «Reset Token».
- O Discord pede minha senha ao gerar o token: é normal, é uma verificação de segurança (passo 2).
- «Falta ativar a opção Message Content Intent»: revise o passo 3 e salve as alterações.
- «O canal do Discord não foi encontrado»: verifique se o bot foi convidado para esse mesmo servidor (passo 4) e se você copiou o link do canal certo (passo 5).
- O chat conecta mas nenhuma mensagem chega: verifique se o bot pode ver esse canal. Em canais privados é preciso dar acesso a ele ou um cargo que o tenha.
