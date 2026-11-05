// 生成 GitHub 奖杯 SVG，由 PersonalStatus.yml 复制到 github-profile-trophy 的
// 代码目录里运行。上游自带的 render_svg.ts 选项是写死的，这里配上主页的颜色。
import { GithubApiService } from "./src/Services/GithubApiService.ts";
import { Card } from "./src/card.ts";
import { COLORS, Theme } from "./src/theme.ts";

const [username, outputPath] = Deno.args;

const theme: Theme = {
  ...COLORS.default,
  BACKGROUND: "#FDF6EF",
  TITLE: "#8E3A59",
  ICON_CIRCLE: "#F6E3D8",
  TEXT: "#6F5B58",
  LAUREL: "#C96F7F",
  NEXT_RANK_BAR: "#C96F7F",
};

const userInfo = await new GithubApiService().requestUserInfo(username);
if (!("totalCommits" in userInfo)) {
  console.error("Failed to fetch user info:", userInfo);
  Deno.exit(1);
}

const maxColumn = 6;
const maxRow = 1;
const panelSize = 110;
const margin = 10;
const noBackground = false;
const noFrame = true;

const card = new Card(
  [],
  [],
  maxColumn,
  maxRow,
  panelSize,
  margin,
  margin,
  noBackground,
  noFrame,
);

await Deno.writeTextFile(outputPath, card.render(userInfo, theme));
console.log(`Wrote ${outputPath}`);
