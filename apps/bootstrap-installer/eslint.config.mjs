import shared from '../../eslint.config.shared.mjs'
import { createRequire } from 'module';

const require = createRequire(import.meta.url);

export default [
  ...shared
];
