# vetube
Leia e gerencie de forma acessível o bate-papo do youtube, TikTok, Kick e twitch em suas próprias transmissões ou nas de seus criadores favoritos.
[demonstração do produto em funcionamento](https://www.youtube.com/watch?v=KljpMJNVYCw)
## Caracteristicas
- Modo automático: leia mensagens de bate-papo em tempo real usando a voz sapy5
- Interface invisível: gerencie chats de qualquer janela usando comandos simples do teclado. Você precisa ter um leitor de tela ativo.
- Leitores suportados:
  - NVDA
JAWS
window eyes
  - Super Nova
system access
  - PC Talker
  - ZDSR
- Possibilidade de configuração de acordo com as necessidades do usuário.
  - ligue ou desligue os sons do programa.
  - ativar ou desativar o modo automático.
  - configura a lista de mensagens na interface invisível.
  - Configure as preferências de voz sapy.
  - personalize atalhos de teclado globais
- altere facilmente o modo de leitura do bate-papo: decida se deseja ler todos os bate-papos ou apenas os de uma categoria específica.
- salve seus shows ao vivo em uma seção de favoritos. repita o chat quantas vezes quiser sem precisar ir procurar o link novamente.
- arquivar uma mensagem: útil ter lembretes.
- Traduza o chat de um streaming para o idioma que você gosta.

## Atalhos do teclado.
### Usando interface invisível.
| ação | combinação de teclas |
| ------------------------- | ----------- |
| Silencie a voz sapy | CTRL+p |
| iniciar/cancelar a captura de outra transmissão ao vivo | Alt shift h |
| ir para a transmissão ao vivo anterior | Control Alt shift seta para a esquerda |
| ir para a próxima transmissão ao vivo | Control Alt shift seta para a direita |
| buffer anterior | Alt shift seta para a esquerda |
| próximo buffer | Alt shift seta para a direita |
| Item anterior | Alt shift seta para cima |
| Próximo item | alt shift seta para baixo |
| Item inicial | alt xift  home |
| Item final | alt xift end|
| arquivar uma mensagem | Alt shift a |
| Copie a mensagem atual | alt xift c |
| Excluir um buffer criado anteriormente | alt xift d |
| adiciona a mensagem ao buffer de favoritos | Alt shift f |
| Ativar ou desativar o modo automático | alt xift r |
| desativar sons do programa | Alt shift p |
| procurar uma palavra entre as mensagens | alt shift b |
| exibe a mensagem atual em uma caixa de texto | Alt shift v |
| invocar editor de teclado vetube      | alt shift k           |
| pausar ou retomar a reprodução ao vivo      | control shift p           |
| avançar a reprodução ao vivo      | control shift seta direita           |
| retroceder a reprodução ao vivo      | control shift seta esquerda           |
| aumentar o volume      | control shift seta para cima           |
| diminuir o volume      | control shift seta para baixo           |

### No histórico de bate-papo:
| ação | combinação de teclas |
| ------------------------- | ----------- |
| Reproduzir mensagem selecionada | espaço |

### Na seção de favoritos:
| ação | combinação de teclas |
| ------------------------- | ----------- |
| acessar um link selecionado | espaço |

## atualizações futuras:
Eu adicionei para futuras atualizações futuras
- Possibilidade de mostrar informações da pessoa com quem você está conversando a partir da interface invisível:- Nome do canal do usuário
  - Entre muitas outras coisas.

## Colaborar na tradução
Se você deseja colaborar traduzindo o VeTube para o seu idioma, precisará instalar as ferramentas de internacionalização.

1.  **Instalar o Babel:**
    ```bash
    pip install Babel
    ```
    *Nota: Certifique-se de instalar o pacote `Babel` (evite pacotes incorretos com tamanhos muito pequenos).*

2.  **Extrair textos para atualizar o modelo (.pot):**
    Se novas strings foram adicionadas ao código, atualize o arquivo de modelo:
    ```bash
    pybabel extract -F babel.cfg -o vetube.pot .
    ```

3.  **Iniciar uma nova tradução:**
    Se você for traduzir para um novo idioma (por exemplo, `it` para italiano):
    ```bash
    pybabel init -i vetube.pot -d locales -l it -D vetube
    ```

4.  **Atualizar traduções existentes:**
    Se o idioma já existe e você atualizou o `.pot`, sincronize os arquivos `.po`:
    ```bash
    pybabel update -i vetube.pot -d locales -D vetube
    ```

5.  **Compilar traduções:**
    Para que o programa reconheça as alterações, compile os arquivos `.po` para `.mo`:
    ```bash
    pybabel compile -d locales -D vetube
    ```

# obrigado:
Eu agradeço:

[4everzyanya](https://www.youtube.com/c/4everzyanya/),

Testador principal do projeto.

[Johan G](https://github.com/JohanAnim),

Quem ajudou a criar a interface gráfica do projeto e corrigir alguns pequenos bugs.

Sei que graças a você esta aplicação continuará melhorando e cada uma de suas ideias e colaborações serão bem-vindas a este projeto que construiremos juntos.

Para idéias, bugs e sugestões, você pode escrever para mim em
cesar.verastegui17@gmail.com
## Links para download.
Com o seu apoio, você ajuda este programa a continuar a crescer.

[Você se junta à nossa causa?](https://www.paypal.com/donate/?hosted_button_id=5ZV23UDDJ4C5U)

[baixar o programa para 64 bits](https://github.com/metalalchemist/VeTube/releases/download/v3.7/VeTube-x64.zip)
[baixe o programa para 32 bits](https://github.com/metalalchemist/VeTube/releases/download/v3.7/VeTube-x86.zip)