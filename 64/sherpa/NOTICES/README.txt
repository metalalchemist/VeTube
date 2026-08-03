Servidor TTS nativo de VeTube (vetube-sherpa-grpc.exe)
======================================================

Proceso separado que sintetiza las voces Piper y Kokoro con sherpa-onnx
(https://github.com/k2-fsa/sherpa-onnx, v1.13.4) detras del mismo protocolo
gRPC que usaba el antiguo servidor sonata. Escrito en Rust; no contiene
Python ni numpy, de modo que el arranque de VeTube nunca depende de el.

Codigo fuente del ejecutable (Apache-2.0):
https://github.com/enzowenterstein-collab/vetube-sherpa-grpc

Componentes redistribuidos:
- sherpa-onnx-c-api.dll             sherpa-onnx (Apache-2.0, ver COPYING - sherpa-onnx)
- onnxruntime.dll,
  onnxruntime_providers_shared.dll  ONNX Runtime de Microsoft (MIT, ver COPYING - onnxruntime)
- espeak-ng-data/                   datos de eSpeak NG para la fonemizacion
                                    (GPL-3.0, ver COPYING - espeak-ng); es el mismo
                                    data que acompana a los modelos del proyecto k2-fsa.

El espeak-ng-data de esta carpeta lo usan las voces Piper del catalogo
rhasspy (que no traen el suyo propio); el modelo Kokoro usa el que viaja
dentro de su carpeta en voices/.
