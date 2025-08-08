; ModuleID = 'original_prefix.bc'
source_filename = "orig_minimal_prefix.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@reached_NL = dso_local global i32 0, align 4, !dbg !0
@.str = private unnamed_addr constant [2 x i8] c"0\00", align 1
@.str.1 = private unnamed_addr constant [22 x i8] c"orig_minimal_prefix.c\00", align 1
@__PRETTY_FUNCTION__.logic_bomb = private unnamed_addr constant [23 x i8] c"int logic_bomb(char *)\00", align 1
@.str.2 = private unnamed_addr constant [2 x i8] c"s\00", align 1

; Function Attrs: noinline nounwind optnone uwtable
define dso_local i32 @logic_bomb(i8* %s) #0 !dbg !13 {
entry:
  %s.addr = alloca i8*, align 8
  %symvar = alloca i32, align 4
  %d = alloca double, align 8
  store i8* %s, i8** %s.addr, align 8
  call void @llvm.dbg.declare(metadata i8** %s.addr, metadata !18, metadata !DIExpression()), !dbg !19
  call void @llvm.dbg.declare(metadata i32* %symvar, metadata !20, metadata !DIExpression()), !dbg !21
  %0 = load i8*, i8** %s.addr, align 8, !dbg !22
  %arrayidx = getelementptr inbounds i8, i8* %0, i64 0, !dbg !22
  %1 = load i8, i8* %arrayidx, align 1, !dbg !22
  %conv = sext i8 %1 to i32, !dbg !22
  %sub = sub nsw i32 %conv, 48, !dbg !23
  store i32 %sub, i32* %symvar, align 4, !dbg !21
  store i32 1, i32* @reached_NL, align 4, !dbg !24
  call void @__assert_fail(i8* getelementptr inbounds ([2 x i8], [2 x i8]* @.str, i64 0, i64 0), i8* getelementptr inbounds ([22 x i8], [22 x i8]* @.str.1, i64 0, i64 0), i32 16, i8* getelementptr inbounds ([23 x i8], [23 x i8]* @__PRETTY_FUNCTION__.logic_bomb, i64 0, i64 0)) #5, !dbg !25
  unreachable, !dbg !25
}

; Function Attrs: nofree nosync nounwind readnone speculatable willreturn
declare void @llvm.dbg.declare(metadata, metadata, metadata) #1

; Function Attrs: noreturn nounwind
declare dso_local void @__assert_fail(i8*, i8*, i32, i8*) #2

; Function Attrs: noinline nounwind optnone uwtable
define dso_local i32 @main() #0 !dbg !26 {
entry:
  %retval = alloca i32, align 4
  %s = alloca [4 x i8], align 1
  store i32 0, i32* %retval, align 4
  call void @llvm.dbg.declare(metadata [4 x i8]* %s, metadata !29, metadata !DIExpression()), !dbg !33
  %arraydecay = getelementptr inbounds [4 x i8], [4 x i8]* %s, i64 0, i64 0, !dbg !34
  call void @klee_make_symbolic(i8* %arraydecay, i64 4, i8* getelementptr inbounds ([2 x i8], [2 x i8]* @.str.2, i64 0, i64 0)), !dbg !35
  %arrayidx = getelementptr inbounds [4 x i8], [4 x i8]* %s, i64 0, i64 0, !dbg !36
  %0 = load i8, i8* %arrayidx, align 1, !dbg !36
  %conv = sext i8 %0 to i32, !dbg !36
  %cmp = icmp sge i32 %conv, 0, !dbg !37
  %conv1 = zext i1 %cmp to i32, !dbg !37
  %conv2 = sext i32 %conv1 to i64, !dbg !36
  call void @klee_assume(i64 %conv2), !dbg !38
  %arraydecay3 = getelementptr inbounds [4 x i8], [4 x i8]* %s, i64 0, i64 0, !dbg !39
  %call = call i32 @logic_bomb(i8* %arraydecay3), !dbg !40
  %1 = load i32, i32* @reached_NL, align 4, !dbg !41
  %tobool = icmp ne i32 %1, 0, !dbg !41
  br i1 %tobool, label %if.end, label %if.then, !dbg !43

if.then:                                          ; preds = %entry
  call void @klee_silent_exit(i32 0) #6, !dbg !44
  unreachable, !dbg !44

if.end:                                           ; preds = %entry
  ret i32 0, !dbg !45
}

declare dso_local void @klee_make_symbolic(i8*, i64, i8*) #3

declare dso_local void @klee_assume(i64) #3

; Function Attrs: noreturn
declare dso_local void @klee_silent_exit(i32) #4

attributes #0 = { noinline nounwind optnone uwtable "frame-pointer"="all" "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #1 = { nofree nosync nounwind readnone speculatable willreturn }
attributes #2 = { noreturn nounwind "frame-pointer"="all" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #3 = { "frame-pointer"="all" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #4 = { noreturn "frame-pointer"="all" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #5 = { noreturn nounwind }
attributes #6 = { noreturn }

!llvm.dbg.cu = !{!2}
!llvm.module.flags = !{!7, !8, !9, !10, !11}
!llvm.ident = !{!12}

!0 = !DIGlobalVariableExpression(var: !1, expr: !DIExpression())
!1 = distinct !DIGlobalVariable(name: "reached_NL", scope: !2, file: !3, line: 9, type: !6, isLocal: false, isDefinition: true)
!2 = distinct !DICompileUnit(language: DW_LANG_C99, file: !3, producer: "clang version 13.0.1 (https://github.com/llvm/llvm-project.git 75e33f71c2dae584b13a7d1186ae0a038ba98838)", isOptimized: false, runtimeVersion: 0, emissionKind: FullDebug, enums: !4, globals: !5, splitDebugInlining: false, nameTableKind: None)
!3 = !DIFile(filename: "orig_minimal_prefix.c", directory: "/home/klee")
!4 = !{}
!5 = !{!0}
!6 = !DIBasicType(name: "int", size: 32, encoding: DW_ATE_signed)
!7 = !{i32 7, !"Dwarf Version", i32 4}
!8 = !{i32 2, !"Debug Info Version", i32 3}
!9 = !{i32 1, !"wchar_size", i32 4}
!10 = !{i32 7, !"uwtable", i32 1}
!11 = !{i32 7, !"frame-pointer", i32 2}
!12 = !{!"clang version 13.0.1 (https://github.com/llvm/llvm-project.git 75e33f71c2dae584b13a7d1186ae0a038ba98838)"}
!13 = distinct !DISubprogram(name: "logic_bomb", scope: !3, file: !3, line: 12, type: !14, scopeLine: 12, flags: DIFlagPrototyped, spFlags: DISPFlagDefinition, unit: !2, retainedNodes: !4)
!14 = !DISubroutineType(types: !15)
!15 = !{!6, !16}
!16 = !DIDerivedType(tag: DW_TAG_pointer_type, baseType: !17, size: 64)
!17 = !DIBasicType(name: "char", size: 8, encoding: DW_ATE_signed_char)
!18 = !DILocalVariable(name: "s", arg: 1, scope: !13, file: !3, line: 12, type: !16)
!19 = !DILocation(line: 12, column: 22, scope: !13)
!20 = !DILocalVariable(name: "symvar", scope: !13, file: !3, line: 13, type: !6)
!21 = !DILocation(line: 13, column: 9, scope: !13)
!22 = !DILocation(line: 13, column: 18, scope: !13)
!23 = !DILocation(line: 13, column: 23, scope: !13)
!24 = !DILocation(line: 15, column: 16, scope: !13)
!25 = !DILocation(line: 16, column: 5, scope: !13)
!26 = distinct !DISubprogram(name: "main", scope: !3, file: !3, line: 26, type: !27, scopeLine: 26, spFlags: DISPFlagDefinition, unit: !2, retainedNodes: !4)
!27 = !DISubroutineType(types: !28)
!28 = !{!6}
!29 = !DILocalVariable(name: "s", scope: !26, file: !3, line: 27, type: !30)
!30 = !DICompositeType(tag: DW_TAG_array_type, baseType: !17, size: 32, elements: !31)
!31 = !{!32}
!32 = !DISubrange(count: 4)
!33 = !DILocation(line: 27, column: 10, scope: !26)
!34 = !DILocation(line: 28, column: 24, scope: !26)
!35 = !DILocation(line: 28, column: 5, scope: !26)
!36 = !DILocation(line: 30, column: 17, scope: !26)
!37 = !DILocation(line: 30, column: 22, scope: !26)
!38 = !DILocation(line: 30, column: 5, scope: !26)
!39 = !DILocation(line: 31, column: 16, scope: !26)
!40 = !DILocation(line: 31, column: 5, scope: !26)
!41 = !DILocation(line: 32, column: 10, scope: !42)
!42 = distinct !DILexicalBlock(scope: !26, file: !3, line: 32, column: 9)
!43 = !DILocation(line: 32, column: 9, scope: !26)
!44 = !DILocation(line: 32, column: 22, scope: !42)
!45 = !DILocation(line: 33, column: 5, scope: !26)
