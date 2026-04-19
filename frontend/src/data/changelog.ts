import releaseBundle from "@repo/releases.json";

export type ChangelogEntry = {
  versao: string;
  data: string;
  titulo: string;
  adicoes: string[];
  correcoes: string[];
};

type ReleaseBundle = {
  changelog: ChangelogEntry[];
  dev_preview_changelog?: ChangelogEntry[];
};

const bundle = releaseBundle as ReleaseBundle;

export const CHANGELOG: ChangelogEntry[] = bundle.changelog ?? [];

export const DEV_PREVIEW_CHANGELOG: ChangelogEntry[] = bundle.dev_preview_changelog ?? [];
