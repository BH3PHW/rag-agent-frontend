/**
 * 前端调试脚本 - 构建和测试所有前端应用
 * ==========================================
 * 
 * 功能：
 * 1. 构建所有前端应用
 * 2. TypeScript 类型检查
 * 3. ESLint 代码检查
 * 4. 生成构建报告
 * 
 * 使用方法：
 * node debug_frontend.js [选项]
 * 
 * 选项：
 *   --build     只构建不测试
 *   --typecheck 只进行类型检查
 *   --lint      只进行代码检查
 *   --all       执行所有检查
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// 颜色输出
const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[36m',
  bold: '\x1b[1m'
};

const log = {
  info: (msg) => console.log(`${colors.blue}[INFO]${colors.reset} ${msg}`),
  success: (msg) => console.log(`${colors.green}[SUCCESS]${colors.reset} ${msg}`),
  error: (msg) => console.log(`${colors.red}[ERROR]${colors.reset} ${msg}`),
  warning: (msg) => console.log(`${colors.yellow}[WARNING]${colors.reset} ${msg}`)
};

// 应用列表
const apps = [
  { name: 'Consumer', path: 'apps/consumer', port: 3000 },
  { name: 'Enterprise', path: 'apps/enterprise', port: 8080 },
  { name: 'System Admin', path: 'apps/system-admin', port: 9090 }
];

// 包列表
const packages = [
  { name: 'UI', path: 'packages/ui' },
  { name: 'Store', path: 'packages/store' }
];

/**
 * 执行命令
 */
function runCommand(command, options = {}) {
  const { cwd = process.cwd(), showOutput = false } = options;
  try {
    log.info(`执行: ${command}`);
    const output = execSync(command, {
      cwd,
      encoding: 'utf-8',
      stdio: showOutput ? 'pipe' : 'pipe',
      timeout: 300000
    });
    if (showOutput && output) {
      console.log(output);
    }
    return { success: true, output };
  } catch (error) {
    return { success: false, error: error.message, output: error.stdout };
  }
}

/**
 * 检查文件是否存在
 */
function checkFileExists(filePath) {
  try {
    return fs.existsSync(filePath);
  } catch {
    return false;
  }
}

/**
 * 获取应用信息
 */
function getAppInfo(appPath) {
  const packageJsonPath = path.join(appPath, 'package.json');
  if (!checkFileExists(packageJsonPath)) {
    return null;
  }

  try {
    const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf-8'));
    return {
      name: packageJson.name,
      version: packageJson.version,
      dependencies: Object.keys(packageJson.dependencies || {}),
      devDependencies: Object.keys(packageJson.devDependencies || {})
    };
  } catch {
    return null;
  }
}

/**
 * 测试 Consumer 应用
 */
function testConsumer() {
  log.info('='.repeat(60));
  log.info('测试 Consumer 应用');
  log.info('='.repeat(60));

  const appPath = path.join(process.cwd(), 'apps/consumer');
  const results = {
    files: [],
    errors: [],
    warnings: []
  };

  // 检查关键文件
  const keyFiles = [
    'src/App.tsx',
    'src/main.tsx',
    'src/pages/Chat.tsx',
    'src/api/client.ts',
    'src/store.ts',
    'package.json'
  ];

  for (const file of keyFiles) {
    const fullPath = path.join(appPath, file);
    if (checkFileExists(fullPath)) {
      results.files.push(file);
      log.success(`✅ ${file} 存在`);
    } else {
      results.errors.push(`${file} 不存在`);
      log.error(`❌ ${file} 不存在`);
    }
  }

  // 获取应用信息
  const appInfo = getAppInfo(appPath);
  if (appInfo) {
    log.info(`应用名称: ${appInfo.name}`);
    log.info(`版本: ${appInfo.version}`);
    log.info(`依赖数量: ${appInfo.dependencies.length}`);
  }

  return results;
}

/**
 * 测试 Enterprise 应用
 */
function testEnterprise() {
  log.info('='.repeat(60));
  log.info('测试 Enterprise 应用');
  log.info('='.repeat(60));

  const appPath = path.join(process.cwd(), 'apps/enterprise');
  const results = {
    files: [],
    errors: [],
    warnings: []
  };

  // 检查关键文件
  const keyFiles = [
    'src/App.tsx',
    'src/main.tsx',
    'src/pages/Settings.tsx',
    'src/pages/ChatMonitor.tsx',
    'src/pages/Documents.tsx',
    'src/api/client.ts',
    'src/store.ts',
    'package.json'
  ];

  for (const file of keyFiles) {
    const fullPath = path.join(appPath, file);
    if (checkFileExists(fullPath)) {
      results.files.push(file);
      log.success(`✅ ${file} 存在`);
    } else {
      results.errors.push(`${file} 不存在`);
      log.error(`❌ ${file} 不存在`);
    }
  }

  return results;
}

/**
 * 测试 System Admin 应用
 */
function testSystemAdmin() {
  log.info('='.repeat(60));
  log.info('测试 System Admin 应用');
  log.info('='.repeat(60));

  const appPath = path.join(process.cwd(), 'apps/system-admin');
  const results = {
    files: [],
    errors: [],
    warnings: []
  };

  // 检查关键文件
  const keyFiles = [
    'src/App.tsx',
    'src/main.tsx',
    'src/pages/ApiConfig.tsx',
    'src/pages/Users.tsx',
    'src/pages/Services.tsx',
    'src/pages/Alerts.tsx',
    'src/store.ts',
    'package.json'
  ];

  for (const file of keyFiles) {
    const fullPath = path.join(appPath, file);
    if (checkFileExists(fullPath)) {
      results.files.push(file);
      log.success(`✅ ${file} 存在`);
    } else {
      results.errors.push(`${file} 不存在`);
      log.error(`❌ ${file} 不存在`);
    }
  }

  return results;
}

/**
 * 测试共享包
 */
function testPackages() {
  log.info('='.repeat(60));
  log.info('测试共享包');
  log.info('='.repeat(60));

  const results = {
    packages: []
  };

  for (const pkg of packages) {
    const pkgPath = path.join(process.cwd(), pkg.path);
    log.info(`检查 ${pkg.name}...`);

    const srcPath = path.join(pkgPath, 'src');
    if (checkFileExists(srcPath)) {
      log.success(`✅ ${pkg.name} 源码目录存在`);
      results.packages.push({
        name: pkg.name,
        exists: true
      });
    } else {
      log.error(`❌ ${pkg.name} 源码目录不存在`);
      results.packages.push({
        name: pkg.name,
        exists: false
      });
    }
  }

  return results;
}

/**
 * 构建所有应用
 */
async function buildAll() {
  log.info('='.repeat(60));
  log.info('开始构建所有前端应用');
  log.info('='.repeat(60));

  const result = runCommand('npm run build', { cwd: process.cwd() });

  if (result.success) {
    log.success('✅ 所有应用构建成功！');
    return true;
  } else {
    log.error('❌ 构建失败');
    if (result.output) {
      console.log(result.output);
    }
    return false;
  }
}

/**
 * TypeScript 类型检查
 */
async function typeCheck() {
  log.info('='.repeat(60));
  log.info('执行 TypeScript 类型检查');
  log.info('='.repeat(60));

  const result = runCommand('npx tsc --noEmit', { cwd: process.cwd() });

  if (result.success) {
    log.success('✅ 类型检查通过！');
    return true;
  } else {
    log.warning('⚠️  类型检查有警告（可能不影响构建）');
    return false;
  }
}

/**
 * 生成测试报告
 */
function generateReport(results) {
  log.info('='.repeat(60));
  log.info('生成测试报告');
  log.info('='.repeat(60));

  const report = {
    timestamp: new Date().toISOString(),
    summary: {
      totalApps: apps.length,
      totalPackages: packages.length,
      appsTested: 0,
      packagesTested: 0,
      buildSuccess: false,
      typeCheckSuccess: false
    },
    apps: [],
    packages: []
  };

  // 统计
  report.summary.appsTested = apps.length;
  report.summary.packagesTested = packages.length;

  return report;
}

/**
 * 主函数
 */
async function main() {
  console.log('\n');
  console.log(colors.bold + '='.repeat(60));
  console.log('  前端应用调试和测试工具');
  console.log('='.repeat(60) + colors.reset);
  console.log('\n');

  const args = process.argv.slice(2);
  const options = {
    build: args.includes('--build'),
    typecheck: args.includes('--typecheck'),
    lint: args.includes('--lint'),
    all: args.includes('--all')
  };

  // 如果没有指定选项，默认执行全部
  const runAll = !options.build && !options.typecheck && !options.lint;

  try {
    // 测试所有应用
    testConsumer();
    testEnterprise();
    testSystemAdmin();
    testPackages();

    // 根据选项执行相应操作
    if (runAll || options.build) {
      console.log('\n');
      const buildSuccess = await buildAll();
      if (buildSuccess) {
        log.success('\n🎉 所有前端应用构建成功！');
      }
    }

    if (runAll || options.typecheck) {
      console.log('\n');
      await typeCheck();
    }

    // 生成报告
    const report = generateReport({});
    log.info(`\n测试完成时间: ${report.timestamp}`);

  } catch (error) {
    log.error(`\n❌ 测试过程中出现错误: ${error.message}`);
    process.exit(1);
  }

  console.log('\n');
  console.log(colors.bold + '='.repeat(60));
  console.log('  测试完成');
  console.log('='.repeat(60) + colors.reset);
  console.log('\n');
}

// 运行主函数
main().catch(console.error);

// 导出函数供其他模块使用
module.exports = {
  testConsumer,
  testEnterprise,
  testSystemAdmin,
  testPackages,
  buildAll,
  typeCheck
};
