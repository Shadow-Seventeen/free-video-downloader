// 模拟完整的API调用和数据流
const mockApiResponse = {
    success: true,
    data: {
        id: "BV1jUgA6YEw6",
        title: "《一本书读懂财报》 上篇：零基础、普通投资者的财报入门课",
        platform: "BiliBili",
        duration: 3627,
        duration_string: "1:00:27",
        uploader: "野生量化员",
        description: "本期《一本书读懂财报（全新修订版）》上篇，带你零基础入门财务报表...",
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
    }
};

// 模拟API调用
async function mockApiCall(url) {
    console.log('模拟API调用:', url);
    // 模拟网络延迟
    await new Promise(resolve => setTimeout(resolve, 100));
    return mockApiResponse;
}

// 模拟App.vue中的handleParse函数
async function handleParse(url) {
    console.log('\n=== 模拟handleParse函数 ===');

    let videoData = null;
    let loading = false;

    try {
        loading = true;
        console.log('开始解析视频...');

        const res = await mockApiCall(url);

        if (res.success) {
            console.log('解析成功！');
            videoData = res.data;
            console.log('videoData:', JSON.stringify(videoData, null, 2));
        } else {
            console.error('解析失败：', res.error);
        }
    } catch (err) {
        console.error('解析失败：', err.message);
    } finally {
        loading = false;
        console.log('解析完成');
    }

    return videoData;
}

// 模拟VideoResult组件的数据流
function simulateVideoResultComponent(videoData) {
    console.log('\n=== 模拟VideoResult组件 ===');

    // 模拟props
    const props = { video: videoData };

    // 模拟响应式数据
    const selectedFormat = ref(
        props.video.formats?.length > 0 ? props.video.formats[0].format_id : ''
    );

    const downloading = ref(false);

    console.log('\n1. 初始状态:');
    console.log('   props.video.formats长度:', props.video.formats?.length || 0);
    console.log('   props.video.formats[0].format_id:', props.video.formats[0]?.format_id);
    console.log('   selectedFormat.value:', JSON.stringify(selectedFormat.value));

    // 模拟模板中的判断逻辑
    const isButtonDisabled = !selectedFormat.value || downloading.value;
    console.log('   下载按钮是否禁用:', isButtonDisabled);

    if (isButtonDisabled) {
        console.log('   ❌ 下载按钮置灰');
    } else {
        console.log('   ✅ 下载按钮可用');
    }

    // 模拟用户交互
    console.log('\n2. 模拟用户点击格式选择:');

    if (props.video.formats) {
        props.video.formats.forEach((fmt, index) => {
            console.log(`   点击格式 ${index + 1}: ${fmt.label}`);

            // 模拟点击事件
            selectedFormat.value = fmt.format_id;

            const newIsDisabled = !selectedFormat.value || downloading.value;
            console.log(`   selectedFormat.value: ${JSON.stringify(selectedFormat.value)}`);
            console.log(`   下载按钮状态: ${newIsDisabled ? '禁用' : '启用'}`);
        });
    }

    // 模拟下载过程
    console.log('\n3. 模拟点击下载按钮:');
    downloading.value = true;
    console.log('   downloading.value = true');
    console.log('   下载按钮状态:', !selectedFormat.value || downloading.value ? '禁用' : '启用');

    // 模拟下载完成
    setTimeout(() => {
        downloading.value = false;
        console.log('   downloading.value = false');
        console.log('   下载按钮状态:', !selectedFormat.value || downloading.value ? '禁用' : '启用');
    }, 1000);
}

// 简单的ref实现
function ref(value) {
    return {
        value: value
    };
}

// 运行测试
async function runTest() {
    console.log('开始测试完整流程...');

    const videoData = await handleParse('https://www.bilibili.com/video/BV1jUgA6YEw6');

    if (videoData) {
        simulateVideoResultComponent(videoData);
    } else {
        console.error('无法获取视频数据');
    }

    console.log('\n测试完成！');
}

// 执行测试
runTest().catch(console.error);