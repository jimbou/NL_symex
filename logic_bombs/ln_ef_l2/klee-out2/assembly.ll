; ModuleID = 'updated.bc'
source_filename = "ln_ef_l2_klee_transformed.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

@.str = private unnamed_addr constant [2 x i8] c"s\00", align 1

; Function Attrs: noinline nounwind optnone uwtable
define dso_local i32 @logic_bomb(i8* %s) #0 !dbg !9 {
entry:
  %retval = alloca i32, align 4
  %s.addr = alloca i8*, align 8
  %symvar = alloca i32, align 4
  %d = alloca double, align 8
  store i8* %s, i8** %s.addr, align 8
  call void @llvm.dbg.declare(metadata i8** %s.addr, metadata !15, metadata !DIExpression()), !dbg !16
  call void @llvm.dbg.declare(metadata i32* %symvar, metadata !17, metadata !DIExpression()), !dbg !18
  %0 = load i8*, i8** %s.addr, align 8, !dbg !19
  %arrayidx = getelementptr inbounds i8, i8* %0, i64 0, !dbg !19
  %1 = load i8, i8* %arrayidx, align 1, !dbg !19
  %conv = sext i8 %1 to i32, !dbg !19
  %sub = sub nsw i32 %conv, 48, !dbg !20
  store i32 %sub, i32* %symvar, align 4, !dbg !18
  %2 = load i32, i32* %symvar, align 4, !dbg !21
  %cmp = icmp sgt i32 %2, 0, !dbg !22
  %conv1 = zext i1 %cmp to i32, !dbg !22
  %conv2 = sext i32 %conv1 to i64, !dbg !21
  call void @klee_assume(i64 %conv2), !dbg !23
  call void @llvm.dbg.declare(metadata double* %d, metadata !24, metadata !DIExpression()), !dbg !26
  %3 = load i32, i32* %symvar, align 4, !dbg !27
  %conv3 = sitofp i32 %3 to double, !dbg !27
  %call = call double @log(double %conv3) #4, !dbg !28
  store double %call, double* %d, align 8, !dbg !26
  %4 = load i32, i32* %symvar, align 4, !dbg !29
  %cmp4 = icmp eq i32 %4, 7, !dbg !31
  br i1 %cmp4, label %if.then, label %if.else, !dbg !32

if.then:                                          ; preds = %entry
  store double 1.945000e+00, double* %d, align 8, !dbg !33
  br label %if.end, !dbg !35

if.else:                                          ; preds = %entry
  store double 0.000000e+00, double* %d, align 8, !dbg !36
  br label %if.end

if.end:                                           ; preds = %if.else, %if.then
  %5 = load double, double* %d, align 8, !dbg !38
  %cmp6 = fcmp olt double 1.940000e+00, %5, !dbg !40
  br i1 %cmp6, label %land.lhs.true, label %if.else11, !dbg !41

land.lhs.true:                                    ; preds = %if.end
  %6 = load double, double* %d, align 8, !dbg !42
  %cmp8 = fcmp olt double %6, 1.950000e+00, !dbg !43
  br i1 %cmp8, label %if.then10, label %if.else11, !dbg !44

if.then10:                                        ; preds = %land.lhs.true
  store i32 1, i32* %retval, align 4, !dbg !45
  br label %return, !dbg !45

if.else11:                                        ; preds = %land.lhs.true, %if.end
  store i32 0, i32* %retval, align 4, !dbg !47
  br label %return, !dbg !47

return:                                           ; preds = %if.else11, %if.then10
  %7 = load i32, i32* %retval, align 4, !dbg !49
  ret i32 %7, !dbg !49
}

; Function Attrs: nofree nosync nounwind readnone speculatable willreturn
declare void @llvm.dbg.declare(metadata, metadata, metadata) #1

declare dso_local void @klee_assume(i64) #2

; Function Attrs: nounwind
declare dso_local double @log(double) #3

; Function Attrs: noinline nounwind optnone uwtable
define dso_local i32 @main(i32 %argc, i8** %argv) #0 !dbg !50 {
entry:
  %retval = alloca i32, align 4
  %argc.addr = alloca i32, align 4
  %argv.addr = alloca i8**, align 8
  %s = alloca [5 x i8], align 1
  store i32 0, i32* %retval, align 4
  store i32 %argc, i32* %argc.addr, align 4
  call void @llvm.dbg.declare(metadata i32* %argc.addr, metadata !54, metadata !DIExpression()), !dbg !55
  store i8** %argv, i8*** %argv.addr, align 8
  call void @llvm.dbg.declare(metadata i8*** %argv.addr, metadata !56, metadata !DIExpression()), !dbg !57
  call void @llvm.dbg.declare(metadata [5 x i8]* %s, metadata !58, metadata !DIExpression()), !dbg !62
  %0 = bitcast [5 x i8]* %s to i8*, !dbg !63
  call void @klee_make_symbolic(i8* %0, i64 5, i8* getelementptr inbounds ([2 x i8], [2 x i8]* @.str, i64 0, i64 0)), !dbg !64
  %arrayidx = getelementptr inbounds [5 x i8], [5 x i8]* %s, i64 0, i64 4, !dbg !65
  %1 = load i8, i8* %arrayidx, align 1, !dbg !65
  %conv = sext i8 %1 to i32, !dbg !65
  %cmp = icmp eq i32 %conv, 0, !dbg !66
  %conv1 = zext i1 %cmp to i32, !dbg !66
  %conv2 = sext i32 %conv1 to i64, !dbg !65
  call void @klee_assume(i64 %conv2), !dbg !67
  %arraydecay = getelementptr inbounds [5 x i8], [5 x i8]* %s, i64 0, i64 0, !dbg !68
  %call = call i32 @logic_bomb(i8* %arraydecay), !dbg !69
  ret i32 %call, !dbg !70
}

declare dso_local void @klee_make_symbolic(i8*, i64, i8*) #2

attributes #0 = { noinline nounwind optnone uwtable "frame-pointer"="all" "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #1 = { nofree nosync nounwind readnone speculatable willreturn }
attributes #2 = { "frame-pointer"="all" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #3 = { nounwind "frame-pointer"="all" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #4 = { nounwind }

!llvm.dbg.cu = !{!0}
!llvm.module.flags = !{!3, !4, !5, !6, !7}
!llvm.ident = !{!8}

!0 = distinct !DICompileUnit(language: DW_LANG_C99, file: !1, producer: "clang version 13.0.1 (https://github.com/llvm/llvm-project.git 75e33f71c2dae584b13a7d1186ae0a038ba98838)", isOptimized: false, runtimeVersion: 0, emissionKind: FullDebug, enums: !2, splitDebugInlining: false, nameTableKind: None)
!1 = !DIFile(filename: "ln_ef_l2_klee_transformed.c", directory: "/home/klee/ln_ef_l2")
!2 = !{}
!3 = !{i32 7, !"Dwarf Version", i32 4}
!4 = !{i32 2, !"Debug Info Version", i32 3}
!5 = !{i32 1, !"wchar_size", i32 4}
!6 = !{i32 7, !"uwtable", i32 1}
!7 = !{i32 7, !"frame-pointer", i32 2}
!8 = !{!"clang version 13.0.1 (https://github.com/llvm/llvm-project.git 75e33f71c2dae584b13a7d1186ae0a038ba98838)"}
!9 = distinct !DISubprogram(name: "logic_bomb", scope: !1, file: !1, line: 11, type: !10, scopeLine: 11, flags: DIFlagPrototyped, spFlags: DISPFlagDefinition, unit: !0, retainedNodes: !2)
!10 = !DISubroutineType(types: !11)
!11 = !{!12, !13}
!12 = !DIBasicType(name: "int", size: 32, encoding: DW_ATE_signed)
!13 = !DIDerivedType(tag: DW_TAG_pointer_type, baseType: !14, size: 64)
!14 = !DIBasicType(name: "char", size: 8, encoding: DW_ATE_signed_char)
!15 = !DILocalVariable(name: "s", arg: 1, scope: !9, file: !1, line: 11, type: !13)
!16 = !DILocation(line: 11, column: 22, scope: !9)
!17 = !DILocalVariable(name: "symvar", scope: !9, file: !1, line: 12, type: !12)
!18 = !DILocation(line: 12, column: 9, scope: !9)
!19 = !DILocation(line: 12, column: 18, scope: !9)
!20 = !DILocation(line: 12, column: 23, scope: !9)
!21 = !DILocation(line: 14, column: 17, scope: !9)
!22 = !DILocation(line: 14, column: 24, scope: !9)
!23 = !DILocation(line: 14, column: 5, scope: !9)
!24 = !DILocalVariable(name: "d", scope: !9, file: !1, line: 15, type: !25)
!25 = !DIBasicType(name: "double", size: 64, encoding: DW_ATE_float)
!26 = !DILocation(line: 15, column: 12, scope: !9)
!27 = !DILocation(line: 15, column: 20, scope: !9)
!28 = !DILocation(line: 15, column: 16, scope: !9)
!29 = !DILocation(line: 16, column: 9, scope: !30)
!30 = distinct !DILexicalBlock(scope: !9, file: !1, line: 16, column: 9)
!31 = !DILocation(line: 16, column: 16, scope: !30)
!32 = !DILocation(line: 16, column: 9, scope: !9)
!33 = !DILocation(line: 17, column: 7, scope: !34)
!34 = distinct !DILexicalBlock(scope: !30, file: !1, line: 16, column: 22)
!35 = !DILocation(line: 18, column: 5, scope: !34)
!36 = !DILocation(line: 19, column: 11, scope: !37)
!37 = distinct !DILexicalBlock(scope: !30, file: !1, line: 18, column: 12)
!38 = !DILocation(line: 21, column: 15, scope: !39)
!39 = distinct !DILexicalBlock(scope: !9, file: !1, line: 21, column: 8)
!40 = !DILocation(line: 21, column: 13, scope: !39)
!41 = !DILocation(line: 21, column: 17, scope: !39)
!42 = !DILocation(line: 21, column: 20, scope: !39)
!43 = !DILocation(line: 21, column: 22, scope: !39)
!44 = !DILocation(line: 21, column: 8, scope: !9)
!45 = !DILocation(line: 22, column: 9, scope: !46)
!46 = distinct !DILexicalBlock(scope: !39, file: !1, line: 21, column: 29)
!47 = !DILocation(line: 24, column: 9, scope: !48)
!48 = distinct !DILexicalBlock(scope: !39, file: !1, line: 23, column: 10)
!49 = !DILocation(line: 26, column: 1, scope: !9)
!50 = distinct !DISubprogram(name: "main", scope: !1, file: !1, line: 28, type: !51, scopeLine: 28, flags: DIFlagPrototyped, spFlags: DISPFlagDefinition, unit: !0, retainedNodes: !2)
!51 = !DISubroutineType(types: !52)
!52 = !{!12, !12, !53}
!53 = !DIDerivedType(tag: DW_TAG_pointer_type, baseType: !13, size: 64)
!54 = !DILocalVariable(name: "argc", arg: 1, scope: !50, file: !1, line: 28, type: !12)
!55 = !DILocation(line: 28, column: 14, scope: !50)
!56 = !DILocalVariable(name: "argv", arg: 2, scope: !50, file: !1, line: 28, type: !53)
!57 = !DILocation(line: 28, column: 27, scope: !50)
!58 = !DILocalVariable(name: "s", scope: !50, file: !1, line: 29, type: !59)
!59 = !DICompositeType(tag: DW_TAG_array_type, baseType: !14, size: 40, elements: !60)
!60 = !{!61}
!61 = !DISubrange(count: 5)
!62 = !DILocation(line: 29, column: 6, scope: !50)
!63 = !DILocation(line: 30, column: 20, scope: !50)
!64 = !DILocation(line: 30, column: 1, scope: !50)
!65 = !DILocation(line: 31, column: 13, scope: !50)
!66 = !DILocation(line: 31, column: 17, scope: !50)
!67 = !DILocation(line: 31, column: 1, scope: !50)
!68 = !DILocation(line: 32, column: 19, scope: !50)
!69 = !DILocation(line: 32, column: 8, scope: !50)
!70 = !DILocation(line: 32, column: 1, scope: !50)
