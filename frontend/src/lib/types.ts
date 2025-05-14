import { LocalAudioTrack, LocalVideoTrack } from "livekit-client";
import { ReactNode } from "react";

export interface SessionProps {
  roomName: string;
  identity: string;
  audioTrack?: LocalAudioTrack;
  videoTrack?: LocalVideoTrack;
  region?: string;
  turnServer?: RTCIceServer;
  forceRelay?: boolean;
}

export interface TokenResult {
  identity: string;
  accessToken: string;
}

export interface HeaderProps {
  startCall: (e: Event) => void;
  endCall: (e: Event) => void;
  isCallActive: boolean;
  toggleDevice: (type: "video" | "audio") => void;
  isLoading: boolean;
  shouldShowDeviceSettings: boolean;
  isVideoInputEnabled: boolean;
  isAudioInputEnabled: boolean;
}

export interface SpeakerAction {
  id: string; 
  content: ReactNode;
}

export interface LLMConfig {
  name: string;
  description: string;
  instructions: string;
  conversationStarters: string[];
  capabilities: {
    webBrowsing: boolean;
    imageGeneration: boolean;
    codeInterpreter: boolean;
  };
  actions: string[];
}