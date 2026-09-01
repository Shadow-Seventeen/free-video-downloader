// 模拟前端VideoResult组件的逻辑
console.log('=== 模拟前端下载按钮逻辑测试 ===');

// 模拟后端返回的数据
const mockVideoData = {
    id: "BV1jUgA6YEw6",
    title: "《一本书读懂财报》 上篇：零基础、普通投资者的财报入门课",
    platform: "BiliBili",
    duration: 3627,
    duration_string: "1:00:27",
    uploader: "野生量化员",
    formats: [
        {
            format_id: "64",
            label: "720p MP4 (23.2MB)",
            resolution: "?x720",
            height: 720,
            filesize: 24342889,
            has_audio: true,
            vcodec: null,
            acodec: null
        },
        {
            format_id: "32",
            label: "480p MP4 (14.0MB)",
            resolution: "?x480",
            height: 480,
            filesize: 14720332,
            has_audio: true,
            vcodec: null,
            acodec: null
        },
        {
            format_id: "16",
            label: "360p MP4 (10.6MB)",
            resolution: "?x360",
            height: 360,
            filesize: 11106476,
            has_audio: true,
            vcodec: null,
            acodec: null
        }
    ]
};

// 模拟Vue的ref行为
function ref(value) {
    return {
        value: value
    };
}

// 模拟VideoResult组件中的逻辑
function simulateVideoResult() {
    console.log('\n1. 初始化props:');
    console.log('   video.formats长度:', mockVideoData.formats?.length || 0);

    console.log('\n2. 初始化selectedFormat:');
    const selectedFormat = ref(
        mockVideoData.formats?.length > 0 ? mockVideoData.formats[0].format_id : ''
    );
    console.log('   selectedFormat.value:', JSON.stringify(selectedFormat.value));

    console.log('\n3. 检查下载按钮状态:');
    const downloading = ref(false);
    console.log('   downloading.value:', downloading.value);
    console.log('   selectedFormat是否存在:', !!selectedFormat.value);
    console.log('   下载按钮是否禁用:', !selectedFormat.value || downloading.value);

    console.log('\n4. 模拟用户点击不同格式:');
    mockVideoData.formats.forEach((fmt, index) => {
        console.log(`\n   选择格式 ${index + 1}: ${fmt.label}`);
        selectedFormat.value = fmt.format_id;
        console.log('   selectedFormat.value:', JSON.stringify(selectedFormat.value));
        console.log('   下载按钮状态:', !selectedFormat.value || downloading.value ? '禁用' : '启用');
    });

    console.log('\n5. 模拟下载过程:');
    console.log('   开始下载...');
    downloading.value = true;
    console.log('   downloading.value:', downloading.value);
    console.log('   下载按钮状态:', !selectedFormat.value || downloading.value ? '禁用' : '启用');

    console.log('\n6. 下载完成:');
    downloading.value = false;
    console.log('   downloading.value:', downloading.value);
    console.log('   下载按钮状态:', !selectedFormat.value || downloading.value ? '禁用' : '启用');
}

// 测试不同场景
function testEdgeCases() {
    console.log('\n=== 测试边界情况 ===');

    // 场景1: formats为空
    console.log('\n1. 场景: formats为空');
    const emptyFormats = { formats: [] };
    const selectedFormat1 = ref(
        emptyFormats.formats?.length > 0 ? emptyFormats.formats[0].format_id : ''
    );
    console.log('   selectedFormat.value:', JSON.stringify(selectedFormat1.value));
    console.log('   下载按钮状态:', !selectedFormat1.value ? '禁用' : '启用');

    // 场景2: formats第一个格式format_id为空
    console.log('\n2. 场景: 第一个格式format_id为空');
    const firstFormatEmpty = {
        formats: [{ format_id: '', label: 'No ID', has_audio: true }]
    };
    const selectedFormat2 = ref(
        firstFormatEmpty.formats?.length > 0 ? firstFormatEmpty.formats[0].format_id : ''
    );
    console.log('   selectedFormat.value:', JSON.stringify(selectedFormat2.value));
    console.log('   下载按钮状态:', !selectedFormat2.value ? '禁用' : '启用');
}

// 执行测试
simulateVideoResult();
testEdgeCases();