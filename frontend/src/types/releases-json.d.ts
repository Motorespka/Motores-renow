declare module "@repo/releases.json" {
  type Entry = {
    versao: string;
    data: string;
    titulo: string;
    adicoes: string[];
    correcoes: string[];
  };
  const value: {
    changelog: Entry[];
    dev_preview_changelog?: Entry[];
  };
  export default value;
}
