import cube from "@cubejs-client/core";
import { CUBE_TOKEN, CUBE_URL } from "../../lib/config";

const cubeApi = cube(CUBE_TOKEN, { apiUrl: CUBE_URL });

export { cubeApi };
