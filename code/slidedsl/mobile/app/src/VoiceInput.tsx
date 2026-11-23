// Ditado do pedido por voz (pt-BR). Usa o reconhecedor do próprio Android.
// Preferência: reconhecimento no aparelho (offline) quando o modelo pt-BR está instalado;
// se não estiver, usa o serviço online do sistema e avisa. O botão "Baixar voz offline"
// pede ao Android para instalar o modelo (Android 13+).
import { useEffect, useRef, useState } from "react";
import { Platform, Pressable, StyleSheet, Text, View } from "react-native";
import {
  ExpoSpeechRecognitionModule,
  useSpeechRecognitionEvent,
} from "expo-speech-recognition";

const LANG = "pt-BR";

type Props = {
  /** Recebe o texto final de cada fala, para acrescentar ao pedido. */
  onFinalText: (text: string) => void;
  /** Texto parcial enquanto a pessoa fala (opcional, só para mostrar). */
  onPartialText?: (text: string) => void;
};

export function normalizeSpoken(text: string): string {
  const t = text.trim().replace(/\s+/g, " ");
  return t ? t[0].toUpperCase() + t.slice(1) : "";
}

export default function VoiceInput({ onFinalText, onPartialText }: Props) {
  const [listening, setListening] = useState(false);
  const [offline, setOffline] = useState<boolean | null>(null);
  const [message, setMessage] = useState("");
  const finalSent = useRef(false);

  useEffect(() => {
    if (Platform.OS !== "android") return;
    ExpoSpeechRecognitionModule.getSupportedLocales({})
      .then((r) => setOffline(r.installedLocales.some((l) => l.toLowerCase() === "pt-br")))
      .catch(() => setOffline(false));
    return () => ExpoSpeechRecognitionModule.abort();
  }, []);

  useSpeechRecognitionEvent("start", () => {
    finalSent.current = false;
    setListening(true);
    setMessage("Ouvindo… fale o pedido.");
  });
  useSpeechRecognitionEvent("end", () => {
    setListening(false);
    setMessage((m) => (m.startsWith("Ouvindo") ? "" : m));
    onPartialText?.("");
  });
  useSpeechRecognitionEvent("result", (event) => {
    const text = event.results[0]?.transcript ?? "";
    if (event.isFinal) {
      if (!finalSent.current && text.trim()) {
        finalSent.current = true;
        onFinalText(normalizeSpoken(text));
      }
      onPartialText?.("");
    } else {
      onPartialText?.(text);
    }
  });
  useSpeechRecognitionEvent("error", (event) => {
    setListening(false);
    const hints: Record<string, string> = {
      "not-allowed": "Permita o uso do microfone nas configurações do app.",
      "no-speech": "Não ouvi nada. Tente de novo.",
      network: "Sem internet e sem voz offline instalada. Toque em “Baixar voz offline”.",
      "language-not-supported": "Português não disponível neste reconhecedor.",
    };
    setMessage(hints[event.error] ?? `Erro na voz: ${event.error}`);
  });

  async function start() {
    const permission = await ExpoSpeechRecognitionModule.requestPermissionsAsync();
    if (!permission.granted) {
      setMessage("Sem permissão para o microfone.");
      return;
    }
    ExpoSpeechRecognitionModule.start({
      lang: LANG,
      interimResults: true,
      continuous: false,
      addsPunctuation: true,
      requiresOnDeviceRecognition: offline === true,
    });
  }

  async function downloadOffline() {
    try {
      const r = await ExpoSpeechRecognitionModule.androidTriggerOfflineModelDownload({
        locale: LANG,
      });
      setMessage(
        r.status === "download_success"
          ? "Voz offline instalada."
          : "Download da voz offline iniciado pelo Android.",
      );
      if (r.status === "download_success") setOffline(true);
    } catch {
      setMessage("Este aparelho não permite baixar a voz offline (precisa de Android 13+).");
    }
  }

  return (
    <View style={styles.box}>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={listening ? "Parar ditado" : "Ditar pedido por voz"}
        onPress={() => (listening ? ExpoSpeechRecognitionModule.stop() : start())}
        style={[styles.mic, listening && styles.micOn]}
      >
        <Text style={styles.micText}>{listening ? "■ Parar" : "🎤 Falar"}</Text>
      </Pressable>
      <Text style={styles.status}>
        {offline === null ? "" : offline ? "Voz: offline (no aparelho)" : "Voz: online (do sistema)"}
      </Text>
      {offline === false && Platform.OS === "android" ? (
        <Pressable onPress={downloadOffline} accessibilityRole="button">
          <Text style={styles.link}>Baixar voz offline</Text>
        </Pressable>
      ) : null}
      {message ? <Text style={styles.message}>{message}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  box: { gap: 6 },
  mic: {
    backgroundColor: "#1F3A68",
    borderRadius: 999,
    paddingVertical: 14,
    alignItems: "center",
  },
  micOn: { backgroundColor: "#B42318" },
  micText: { color: "#FFFFFF", fontSize: 18, fontWeight: "600" },
  status: { color: "#475467", fontSize: 13 },
  link: { color: "#1F3A68", fontSize: 14, textDecorationLine: "underline" },
  message: { color: "#344054", fontSize: 14 },
});
