<#
.SYNOPSIS
获取Git仓库的提交历史信息并设置为GitHub Actions环境变量

.DESCRIPTION
此脚本用于GitHub Actions工作流中获取提交历史信息，
并将结果设置为环境变量供后续步骤使用。

.PARAMETER TagName
必需参数，指定要获取提交历史的标签名称。

.EXAMPLE
PS> .\get_commit_history.ps1 -TagName v0.0.6.3
#>
param (
    [Parameter(Mandatory=$true)]
    [string]$TagName
)

# 配置git log格式
# 使用单引号避免PowerShell解析%符号
$format = '- %s (%an)'

# 初始化COMMITS变量
$COMMITS = ""

# 尝试获取提交历史
try {
    # 输出当前标签信息用于调试
    Write-Host "Current tag: $TagName"
    
    # 获取所有标签并进行语义化版本排序
    # 使用git tag --list获取所有标签，然后通过自定义脚本进行正确排序
    $ALL_TAGS = git tag --list
    Write-Host "All tags found: $ALL_TAGS"
    
    # 使用更可靠的方法查找上一个标签
    # 1. 先尝试使用git describe来找上一个标签（更可靠的git内部方法）
    $LAST_TAG = git describe --tags --abbrev=0 ${TagName}^ 2>$null
    
    if ($LAST_TAG) {
        Write-Host "Last tag found: $LAST_TAG"
        # 使用正确的git log语法获取两个标签之间的提交
        Write-Host "Running git log command between $LAST_TAG and $TagName"
        # 在PowerShell中使用更可靠的方式执行git命令并捕获输出
        $logCommand = 'git log ' + $LAST_TAG + '..' + $TagName + ' --pretty=format:"' + $format + '"'
        Write-Host "Executing: $logCommand"
        $COMMITS = Invoke-Expression -Command $logCommand | Out-String
        # 去除首尾空白字符
        $COMMITS = $COMMITS.Trim()
        
        Write-Host ('Commits between ' + $LAST_TAG + ' and ' + $TagName + ':')
        Write-Host $COMMITS
        
        # 如果上一个标签和当前标签之间确实没有提交，使用明确消息
        if (-not $COMMITS) {
            # 使用字符串连接避免变量解析问题
            $COMMITS = '- ' + $LAST_TAG + '到' + $TagName + '之间没有新提交'
        }
    } else {
        # 如果没有上一个标签，说明这是第一个版本或没有其他标签
        Write-Host "No previous tag found, trying to get all commits for current tag"
        # 尝试获取当前标签的所有提交
        $logCommand = 'git log ' + $TagName + ' --pretty=format:"' + $format + '"'
        Write-Host "Executing: $logCommand"
        $COMMITS = Invoke-Expression -Command $logCommand | Out-String
        $COMMITS = $COMMITS.Trim()
        Write-Host $COMMITS
        
        if (-not $COMMITS) {
            # 如果当前标签也没有提交，则获取最近10条提交
            Write-Host "No commits found for current tag, getting latest 10 commits"
            $logCommand = 'git log -n 10 --pretty=format:"' + $format + '"'
            Write-Host "Executing: $logCommand"
            $COMMITS = Invoke-Expression -Command $logCommand | Out-String
            $COMMITS = $COMMITS.Trim()
            Write-Host $COMMITS
        }
        
        # 确保COMMITS不为空，提供默认消息
        if (-not $COMMITS) {
            $COMMITS = "- 暂无提交信息"
        }
    }
} catch {
    Write-Host ('Error fetching commit history: ' + $_)
    # 使用字符串连接避免变量解析问题
    $COMMITS = '- 获取提交历史时出错: ' + $_
}

# 使用正确的PowerShell语法设置环境变量，确保多行内容正确传递
# 使用字符串连接方式确保变量正确展开
$commitContent = 'commits<<COMMIT_EOF' + "`n" + $COMMITS + "`nCOMMIT_EOF"

# 输出到GitHub环境变量文件
Write-Output $commitContent | Out-File -FilePath $env:GITHUB_ENV -Append -Encoding utf8